"""
Django Management Command: reset_cyber_data
Membersihkan (reset) data transaksional atau data kompetisi secara aman.
"""

from django.core.management.base import BaseCommand
from services.data_factory_service import CyberDataFactoryService


class Command(BaseCommand):
    help = "Mereset data kompetisi atau transaksi sesi ujian secara aman (pertahankan akun developer & superadmin)."

    def add_arguments(self, parser):
        parser.add_argument(
            '--attempts-only',
            action='store_true',
            help='Hanya bersihkan sesi ujian, jawaban, dan nilai (soal & kompetisi tetap utuh).'
        )
        parser.add_argument(
            '--yes',
            action='store_true',
            help='Lewati konfirmasi terminal.'
        )

    def handle(self, *args, **options):
        attempts_only = options.get('attempts_only', False)

        if not options.get('yes'):
            target_desc = "SELURUH SESI UJIAN DAN JAWABAN PESERTA" if attempts_only else "SELURUH DATA KOMPETISI, SOAL, DAN PESERTA (Akun Admin & Developer aman)"
            confirm = input(f"Apakah Anda yakin ingin mereset {target_desc}? (ketik 'yes' untuk konfirmasi): ")
            if confirm.strip().lower() != 'yes':
                self.stdout.write(self.style.ERROR("Aksi reset dibatalkan."))
                return

        if attempts_only:
            self.stdout.write(self.style.WARNING("Membersihkan sesi ujian, jawaban, dan evaluasi..."))
            counts = CyberDataFactoryService.reset_attempts_and_scores()
            self.stdout.write(self.style.SUCCESS(f"[OK] Berhasil mereset transaksi ujian: {counts}"))
        else:
            self.stdout.write(self.style.WARNING("Mereset data kompetisi, bank soal, dan peserta dummy..."))
            counts = CyberDataFactoryService.reset_all_competition_data()
            self.stdout.write(self.style.SUCCESS(f"[OK] Berhasil mereset seluruh data kompetisi: {counts}"))
