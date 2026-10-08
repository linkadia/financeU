# FinancU Backend

Django + Django REST Framework backend for FinancU.

## Desarrollo en red local

1. Copia `.env.example` a `.env`.
2. Cambia `192.168.0.192` por la IPv4 de tu ordenador si ha cambiado.
3. Arranca Django escuchando en la red local:

```bash
python manage.py runserver 0.0.0.0:8001
```

Desde otro dispositivo en la misma Wi-Fi, la API estará en:

```text
http://192.168.0.192:8001/api/
```

## Alta por móvil desde LKTrack

FinancU recibe los pagos confirmados en `POST /api/users/integration/subscription-events/`, usando la firma HMAC-SHA-256 existente en `X-Finanu-Signature` con `INTEGRATOR_WEBHOOK_SECRET`. El equipo de LKTrack implementa el envío desde la LP; este repositorio solo recibe y valida el evento.

En eventos `created` o `renewed` posteriores al cobro, `subscription.status` debe ser `active` y `customer.msisdn_hash` debe contener exactamente 64 caracteres hexadecimales minúsculos: SHA-256 del número polaco normalizado como `48` seguido de 9 dígitos. Vector compartido: `48500000000` produce `8fb9d70275a9b255efeaea4fb5a467960e5ab642896e015ed1b0495831c79bc1` (equivalente a `SHA2('48500000000', 256)` en MySQL).

El hash anterior solo es necesario para habilitar el alta por móvil. Las otras operadoras pueden mantener el alta por `signup_token` sin enviar móvil ni hash: el token identifica la suscripción y el backend copia su TID/SID al usuario. La confirmación de pago (`subscription.status = active`) y el cálculo del periodo mensual no dependen del móvil ni de `MSISDN_HMAC_KEY` cuando el evento no incluye hash. Cancelaciones y nuevos pagos se vinculan mediante el mismo TID/SID.

El resto del evento conserva el contrato actual (`event_id`, `event_type`, `occurred_at`, `tid`, `sid` y, opcionalmente, `subscription.access_until`). Si no llega `access_until` en un pago confirmado, FinancU calcula el fin del periodo como un mes natural después de `occurred_at`, ajustando al último día del mes si el día de origen no existe en el mes siguiente. Esta fecha se conserva en la suscripción para calcular el periodo abonado; no limita el acceso de un usuario activo. El webhook acepta eventos antiguos sin `customer.msisdn_hash`, pero esos eventos solo habilitan el registro mediante token.

Los usuarios activos tienen `fecha_renovacion = null` (acceso indefinido hasta recibir una cancelación). Al recibir `cancelled`, el usuario pasa a inactivo y `fecha_renovacion` se fija al final del periodo mensual pagado, con fecha de fin exclusiva. Una fecha explícita de `subscription.access_until` prevalece; si no llega, se calcula el siguiente aniversario mensual del último pago confirmado respecto a la fecha de cancelación, conservando una fecha abonada posterior si ya existe. Ejemplo: cobro el 8 de octubre y cancelación el 20 de octubre permiten entrar hasta el 7 de noviembre inclusive. Mientras no haya cancelación, se presupone continuidad de los cobros mensuales. Una cancelación repetida sin fecha explícita no extiende el periodo. Un nuevo evento de pago reactiva la misma cuenta y vuelve a dejar `fecha_renovacion = null`.

La app consulta `GET /api/users/profiles/{id}/subscription-status/` al entrar en una ruta privada, al recuperar el foco y cada minuto. Si `can_access` es falso, elimina la sesión guardada y vuelve al login. El login también bloquea al usuario inactivo cuyo periodo ya terminó. La migración `0009` elimina las fechas de vencimiento de los usuarios activos existentes, sin cambiar las de los usuarios cancelados.

FinancU requiere `MSISDN_HMAC_KEY`, una clave estable e independiente de `INTEGRATOR_WEBHOOK_SECRET`. Antes de persistir el SHA recibido, calcula `v1:` + `HMAC-SHA256(MSISDN_HMAC_KEY, ASCII(SHA-256 hexadecimal minúsculo))`. Guarda solo esa huella protegida; excluye el SHA enviado por LKTrack del historial de eventos. La pantalla de registro envía el número al backend por HTTPS únicamente cuando no hay token válido. El backend calcula el mismo valor y vincula una única suscripción abonada y sin reclamar. Cambiar `MSISDN_HMAC_KEY` sin migrar las huellas existentes impedirá esas comparaciones.

La migración de este cambio elimina los antiguos valores de `SubscriptionEntitlement.msisdn_hash`, cuyo algoritmo no estaba especificado, y retira `customer.msisdn_hash` del historial anterior. Los usuarios afectados conservan la vía de registro con token hasta que llegue un evento con el formato nuevo.
