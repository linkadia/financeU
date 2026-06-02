import html
import re
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from learning.models import Lesson


PALETTES = {
    "personal-finance": ("#12324a", "#f2ae2e", "#fff3cf"),
    "economics": ("#172033", "#51e178", "#dbeafe"),
    "investing": ("#123728", "#4be277", "#d7fff2"),
    "crypto": ("#2b1855", "#f7931a", "#f7e9ff"),
    "forex": ("#17324a", "#38bdf8", "#e0f2fe"),
}


class Command(BaseCommand):
    help = "Generates local SVG covers for fixed learning lessons without their own media image."

    def handle(self, *args, **options):
        base_dir = Path(settings.BASE_DIR).parent
        output_dir = base_dir / "frontend" / "public" / "learning" / "lesson-covers"
        output_dir.mkdir(parents=True, exist_ok=True)

        updated = 0
        lessons = Lesson.objects.select_related("course", "category", "course__category").order_by(
            "course__language",
            "course__order",
            "course__title",
            "order",
            "title",
        )
        for lesson in lessons:
            if lesson.youtube_video_id:
                continue

            category_slug = self.category_slug(lesson)
            primary, accent, soft = PALETTES.get(category_slug, PALETTES["personal-finance"])
            file_path = output_dir / f"{self.cover_slug(lesson)}.svg"
            public_path = f"/learning/lesson-covers/{file_path.name}"

            file_path.write_text(
                self.render_svg(
                    lesson=lesson,
                    category_slug=category_slug,
                    primary=primary,
                    accent=accent,
                    soft=soft,
                ),
                encoding="utf-8",
            )
            Lesson.objects.filter(id=lesson.id).update(image_url=public_path)
            updated += 1

        self.stdout.write(
            self.style.SUCCESS(f"Generated and assigned {updated} learning lesson covers.")
        )

    def category_slug(self, lesson):
        if lesson.category_id:
            return lesson.category.slug
        if lesson.course.category_id:
            return lesson.course.category.slug
        return "personal-finance"

    def cover_slug(self, lesson):
        raw = f"{lesson.course.language}-{lesson.course.order:02d}-{lesson.course_id}-{lesson.order:02d}-{lesson.title.lower()}"
        return re.sub(r"[^a-z0-9]+", "-", raw).strip("-")[:110]

    def render_svg(self, lesson, category_slug, primary, accent, soft):
        title = html.escape(lesson.title)
        motif = self.render_motif(lesson.content_type, category_slug, accent, soft)

        return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 675" role="img" aria-labelledby="title desc">
  <title id="title">{title}</title>
  <desc id="desc">Decorative learning lesson cover</desc>
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{primary}"/>
      <stop offset="1" stop-color="#080d18"/>
    </linearGradient>
    <radialGradient id="glow" cx="72%" cy="24%" r="62%">
      <stop offset="0" stop-color="{accent}" stop-opacity=".68"/>
      <stop offset="1" stop-color="{accent}" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <rect width="1200" height="675" fill="url(#bg)"/>
  <rect width="1200" height="675" fill="url(#glow)"/>
  <path d="M0 535 C205 430 350 585 565 510 C780 435 905 315 1200 385 V675 H0 Z" fill="{accent}" opacity=".14"/>
  {motif}
</svg>
"""

    def render_motif(self, content_type, category_slug, accent, soft):
        if content_type == "podcast" or content_type == "audio":
            return f"""
  <circle cx="600" cy="330" r="170" fill="{soft}" opacity=".14"/>
  <path d="M445 340 Q445 215 600 215 Q755 215 755 340" fill="none" stroke="{accent}" stroke-width="34" stroke-linecap="round"/>
  <rect x="385" y="325" width="82" height="165" rx="38" fill="{soft}" opacity=".55"/>
  <rect x="733" y="325" width="82" height="165" rx="38" fill="{soft}" opacity=".55"/>
  <path d="M565 405 H635 M600 405 V500" stroke="{accent}" stroke-width="28" stroke-linecap="round"/>
"""
        if content_type == "article":
            return f"""
  <rect x="350" y="140" width="500" height="390" rx="34" fill="{soft}" opacity=".17"/>
  <rect x="410" y="210" width="270" height="28" rx="14" fill="{accent}" opacity=".85"/>
  <rect x="410" y="285" width="380" height="22" rx="11" fill="{soft}" opacity=".55"/>
  <rect x="410" y="340" width="320" height="22" rx="11" fill="{soft}" opacity=".4"/>
  <rect x="410" y="395" width="355" height="22" rx="11" fill="{soft}" opacity=".48"/>
  <circle cx="790" cy="220" r="46" fill="{accent}" opacity=".75"/>
"""
        if content_type == "course":
            return f"""
  <path d="M285 260 L600 125 L915 260 L600 395 Z" fill="{accent}" opacity=".8"/>
  <path d="M390 320 V445 Q600 540 810 445 V320" fill="{soft}" opacity=".24"/>
  <path d="M915 260 V405" stroke="{soft}" stroke-width="18" stroke-linecap="round" opacity=".7"/>
  <circle cx="915" cy="430" r="24" fill="{soft}" opacity=".75"/>
  <rect x="480" y="455" width="240" height="26" rx="13" fill="{accent}" opacity=".75"/>
"""
        if content_type == "tool":
            return f"""
  <rect x="335" y="150" width="530" height="370" rx="42" fill="{soft}" opacity=".14"/>
  <circle cx="465" cy="280" r="58" fill="{accent}" opacity=".8"/>
  <circle cx="600" cy="280" r="58" fill="{soft}" opacity=".4"/>
  <circle cx="735" cy="280" r="58" fill="{accent}" opacity=".55"/>
  <path d="M430 410 H770 M500 470 H700" stroke="{soft}" stroke-width="28" stroke-linecap="round" opacity=".6"/>
"""
        if category_slug == "crypto":
            return f"""
  <polygon points="600,115 805,235 805,475 600,595 395,475 395,235" fill="none" stroke="{accent}" stroke-width="22"/>
  <circle cx="600" cy="355" r="108" fill="{soft}" opacity=".2"/>
  <path d="M535 300 H635 Q695 300 695 355 Q695 410 635 410 H535 M570 260 V450 M635 260 V450" stroke="{soft}" stroke-width="22" stroke-linecap="round" fill="none"/>
"""
        if category_slug == "forex":
            return f"""
  <path d="M310 285 H860 Q930 285 930 355 Q930 425 860 425 H390" fill="none" stroke="{accent}" stroke-width="30" stroke-linecap="round"/>
  <path d="M425 205 L310 285 L425 365 M815 345 L930 425 L815 505" fill="none" stroke="{accent}" stroke-width="30" stroke-linecap="round" stroke-linejoin="round"/>
  <circle cx="490" cy="425" r="70" fill="{soft}" opacity=".24"/>
  <circle cx="740" cy="285" r="70" fill="{soft}" opacity=".24"/>
"""
        return f"""
  <rect x="290" y="380" width="96" height="130" rx="18" fill="{soft}" opacity=".3"/>
  <rect x="450" y="300" width="96" height="210" rx="18" fill="{accent}" opacity=".7"/>
  <rect x="610" y="220" width="96" height="290" rx="18" fill="{soft}" opacity=".42"/>
  <rect x="770" y="150" width="96" height="360" rx="18" fill="{accent}" opacity=".88"/>
  <path d="M300 245 L500 190 L650 230 L835 120" fill="none" stroke="{soft}" stroke-width="18" stroke-linecap="round" stroke-linejoin="round"/>
"""
