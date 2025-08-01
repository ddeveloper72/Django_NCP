# Generated by Django 5.2.4 on 2025-07-28 10:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("smp_client", "0002_signingcertificate_documenttemplate_smpdocument"),
    ]

    operations = [
        migrations.AddField(
            model_name="signingcertificate",
            name="signature_algorithm",
            field=models.CharField(
                blank=True, help_text="Certificate signature algorithm", max_length=100
            ),
        ),
        migrations.AddField(
            model_name="signingcertificate",
            name="validation_status",
            field=models.CharField(
                choices=[
                    ("valid", "Valid"),
                    ("expired", "Expired"),
                    ("invalid", "Invalid"),
                    ("warning", "Valid with Warnings"),
                ],
                default="invalid",
                help_text="Validation status after certificate check",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="signingcertificate",
            name="validation_warnings",
            field=models.TextField(
                blank=True, help_text="Validation warnings and notices"
            ),
        ),
        migrations.AlterField(
            model_name="signingcertificate",
            name="fingerprint",
            field=models.CharField(
                blank=True, help_text="SHA-256 fingerprint", max_length=100
            ),
        ),
        migrations.AlterField(
            model_name="signingcertificate",
            name="is_default",
            field=models.BooleanField(
                default=False, help_text="Use as default signing certificate"
            ),
        ),
        migrations.AlterField(
            model_name="signingcertificate",
            name="issuer",
            field=models.CharField(
                blank=True, help_text="Extracted from certificate", max_length=500
            ),
        ),
        migrations.AlterField(
            model_name="signingcertificate",
            name="serial_number",
            field=models.CharField(
                blank=True, help_text="Extracted from certificate", max_length=100
            ),
        ),
        migrations.AlterField(
            model_name="signingcertificate",
            name="subject",
            field=models.CharField(
                blank=True, help_text="Extracted from certificate", max_length=500
            ),
        ),
        migrations.AlterField(
            model_name="signingcertificate",
            name="valid_from",
            field=models.DateTimeField(
                blank=True, help_text="Certificate valid from date", null=True
            ),
        ),
        migrations.AlterField(
            model_name="signingcertificate",
            name="valid_to",
            field=models.DateTimeField(
                blank=True, help_text="Certificate valid until date", null=True
            ),
        ),
    ]
