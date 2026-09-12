"""
Django Management Command: seed_cyber_data
Mengisi data dummy siber (CTF, Tantangan Hacker, Juri, Sesi Live, Evaluasi) yang realistis.
"""

from django.core.management.base import BaseCommand
from services.data_factory_service import CyberDataFactoryService


class Command(BaseCommand):
    help = "Menyuntikkan data dummy kompetisi siber (CTF) yang ultra-relevan dan lengkap."

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Bersihkan transaksi sesi dan jawaban sebelum melakukan seeding.'
        )
        parser.add_argument(
            '--reset-all',
            action='store_true',
            help='Reset total (kompetisi, soal, peserta) sebelum melakukan seeding.'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("[*] Memulai injeksi data dummy siber (Cyber Data Factory)..."))

        if options.get('reset_all'):
            self.stdout.write(self.style.WARNING("[!] Menjalankan reset total data kompetisi..."))
            cleaned = CyberDataFactoryService.reset_all_competition_data()
            self.stdout.write(self.style.SUCCESS(f"[OK] Data lama berhasil dibersihkan: {cleaned}"))
        elif options.get('reset'):
            self.stdout.write(self.style.WARNING("[!] Membersihkan sesi ujian dan lembar jawaban lama..."))
            cleaned = CyberDataFactoryService.reset_attempts_and_scores()
            self.stdout.write(self.style.SUCCESS(f"[OK] Transaksi lama dibersihkan: {cleaned}"))

        summary = CyberDataFactoryService.seed_realistic_cyber_data()

        self.stdout.write(self.style.SUCCESS("\n========================================================"))
        self.stdout.write(self.style.SUCCESS("[OK] INJEKSI DATA DUMMY SIBER BERHASIL DIEKSEKUSI!"))
        self.stdout.write(self.style.SUCCESS("========================================================"))
        for key, val in summary.items():
            self.stdout.write(f"  - {key.replace('_', ' ').title()}: {val}")
        self.stdout.write(self.style.SUCCESS("========================================================\n"))
