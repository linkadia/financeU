import html
import re
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from learning.models import Course


PALETTES = {
    "personal-finance": ("#113f67", "#f2ae2e", "#d6f5e3"),
    "economics": ("#1f2937", "#51e178", "#dbeafe"),
    "investing": ("#143d2c", "#4be277", "#e6fffb"),
    "crypto": ("#2f1b60", "#f7931a", "#f7e9ff"),
    "forex": ("#19324d", "#38bdf8", "#e0f2fe"),
}


class Command(BaseCommand):
    help = "Regenerates distinct local SVG covers for the current fixed learning catalog."

    def handle(self, *args, **options):
        base_dir = Path(settings.BASE_DIR).parent
        output_dir = base_dir / "frontend" / "public" / "learning" / "course-covers"
        output_dir.mkdir(parents=True, exist_ok=True)

        updated = 0
        courses = Course.objects.select_related("category").order_by("language", "order", "title")
        for course in courses:
            category_slug = course.category.slug if course.category_id else "personal-finance"
            primary, accent, soft = PALETTES.get(category_slug, PALETTES["personal-finance"])
            file_slug = self.cover_slug(course)
            file_path = output_dir / f"{file_slug}.svg"
            public_path = f"/learning/course-covers/{file_path.name}"

            file_path.write_text(
                self.render_svg(
                    course=course,
                    category_slug=category_slug,
                    primary=primary,
                    accent=accent,
                    soft=soft,
                ),
                encoding="utf-8",
            )

            Course.objects.filter(id=course.id).update(
                thumbnail_url=public_path,
                cover_image_url=public_path,
            )
            updated += 1

        self.stdout.write(
            self.style.SUCCESS(f"Generated and assigned {updated} learning course covers.")
        )

    def cover_slug(self, course):
        raw = f"{course.language}-{course.order:02d}-{course.title.lower()}"
        return re.sub(r"[^a-z0-9]+", "-", raw).strip("-")[:96]

    def render_svg(self, course, category_slug, primary, accent, soft):
        title = html.escape(course.title)
        motif = self.render_motif(category_slug, accent, soft)

        return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 675" role="img" aria-labelledby="title desc">
  <title id="title">{title}</title>
  <desc id="desc">Decorative learning course cover</desc>
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{primary}"/>
      <stop offset="1" stop-color="#0b1020"/>
    </linearGradient>
    <radialGradient id="glow" cx="76%" cy="28%" r="60%">
      <stop offset="0" stop-color="{accent}" stop-opacity=".72"/>
      <stop offset="1" stop-color="{accent}" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <rect width="1200" height="675" fill="url(#bg)"/>
  <rect width="1200" height="675" fill="url(#glow)"/>
  <circle cx="1040" cy="110" r="230" fill="{accent}" opacity=".08"/>
  <circle cx="135" cy="600" r="280" fill="#ffffff" opacity=".045"/>
  <path d="M0 500 C180 420 300 610 520 520 S870 360 1200 455 V675 H0 Z" fill="{accent}" opacity=".16"/>
  {motif}
</svg>
"""

    def render_motif(self, category_slug, accent, soft):
        if category_slug == "personal-finance":
            return f"""
  <circle cx="365" cy="315" r="132" fill="{accent}" opacity=".9"/>
  <circle cx="365" cy="315" r="86" fill="#07111f" opacity=".18"/>
  <path d="M655 205 H955 Q990 205 990 240 V455 Q990 490 955 490 H655 Q620 490 620 455 V240 Q620 205 655 205 Z" fill="{soft}" opacity=".18"/>
  <path d="M660 278 H960 M660 348 H890 M660 418 H930" stroke="{soft}" stroke-width="24" stroke-linecap="round" opacity=".6"/>
  <path d="M285 315 H445 M365 235 V395" stroke="#07111f" stroke-width="28" stroke-linecap="round" opacity=".45"/>
"""
        if category_slug == "economics":
            return f"""
  <path d="M210 470 C360 250 520 240 650 420 S900 540 1030 220" fill="none" stroke="{accent}" stroke-width="28" stroke-linecap="round"/>
  <path d="M210 220 C360 440 520 450 650 270 S900 150 1030 470" fill="none" stroke="{soft}" stroke-width="20" stroke-linecap="round" opacity=".75"/>
  <line x1="190" y1="505" x2="1045" y2="505" stroke="{soft}" stroke-width="6" opacity=".35"/>
  <line x1="190" y1="165" x2="190" y2="505" stroke="{soft}" stroke-width="6" opacity=".35"/>
  <circle cx="650" cy="345" r="34" fill="{accent}"/>
"""
        if category_slug == "investing":
            return f"""
  <rect x="235" y="330" width="90" height="165" rx="18" fill="{soft}" opacity=".28"/>
  <rect x="380" y="255" width="90" height="240" rx="18" fill="{accent}" opacity=".75"/>
  <rect x="525" y="190" width="90" height="305" rx="18" fill="{soft}" opacity=".38"/>
  <rect x="670" y="120" width="90" height="375" rx="18" fill="{accent}" opacity=".92"/>
  <path d="M250 230 L438 180 L570 210 L735 105 L965 150" fill="none" stroke="{soft}" stroke-width="18" stroke-linecap="round" stroke-linejoin="round"/>
  <path d="M915 112 L965 150 L905 178" fill="none" stroke="{soft}" stroke-width="18" stroke-linecap="round" stroke-linejoin="round"/>
"""
        if category_slug == "crypto":
            return f"""
  <polygon points="600,92 845,235 845,520 600,663 355,520 355,235" fill="{accent}" opacity=".22"/>
  <polygon points="600,145 795,260 795,495 600,610 405,495 405,260" fill="none" stroke="{accent}" stroke-width="18"/>
  <circle cx="600" cy="378" r="120" fill="{soft}" opacity=".22"/>
  <path d="M520 312 H635 Q705 312 705 372 Q705 432 635 432 H520 M560 262 V492 M635 262 V492" fill="none" stroke="{soft}" stroke-width="24" stroke-linecap="round"/>
"""
        if category_slug == "forex":
            return f"""
  <path d="M285 260 H870 Q955 260 955 345 Q955 430 870 430 H360" fill="none" stroke="{accent}" stroke-width="32" stroke-linecap="round"/>
  <path d="M410 180 L285 260 L410 340 M830 350 L955 430 L830 510" fill="none" stroke="{accent}" stroke-width="32" stroke-linecap="round" stroke-linejoin="round"/>
  <circle cx="430" cy="430" r="82" fill="{soft}" opacity=".25"/>
  <circle cx="760" cy="260" r="82" fill="{soft}" opacity=".25"/>
  <path d="M392 430 H468 M760 222 V298 M722 260 H798" stroke="{soft}" stroke-width="18" stroke-linecap="round"/>
"""
        return f"""
  <circle cx="600" cy="340" r="170" fill="{accent}" opacity=".22"/>
  <path d="M430 430 L550 310 L650 385 L800 210" fill="none" stroke="{soft}" stroke-width="24" stroke-linecap="round" stroke-linejoin="round"/>
"""
