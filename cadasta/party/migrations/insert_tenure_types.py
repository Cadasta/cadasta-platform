from django.db import migrations

from ..models import TenureRelationshipType


class Migration(migrations.Migration):

    def insert_tenure_relationship_types(apps, schema_editor):
        TENURE_RELATIONSHIP_TYPES = (('AL', 'All Types'),
                                     ('CR', 'Carbon Rights'),
                                     ('CO', 'Concessionary Rights'),
                                     ('CU', 'Customary Rights'),
                                     ('EA', 'Easement'),
                                     ('ES', 'Equitable Servitude'),
                                     ('FH', 'Freehold'),
                                     ('GR', 'Grazing Rights'),
                                     ('HR', 'Hunting/Fishing/Harvest Rights'),
                                     ('IN', 'Indigenous Land Rights'),
                                     ('JT', 'Joint Tenancy'),
                                     ('LH', 'Leasehold'),
                                     ('LL', 'Longterm Leasehold'),
                                     ('MR', 'Mineral Rights'),
                                     ('OC',
                                      'Occupancy (No Documented Rights)'
                                      ),
                                     ('TN', 'Tenancy (Documented Sub-lease)'),
                                     ('TC', 'Tenancy In Common'),
                                     ('UC', 'Undivided Co-ownership'),
                                     ('WR', 'Water Rights'))
        for tr_type in TENURE_RELATIONSHIP_TYPES:
            TenureRelationshipType.objects.create(
                id=tr_type[0], label=tr_type[1])

    dependencies = [
        ('party', '0002_tenure_relationships'),
    ]

    operations = [
        migrations.RunPython(insert_tenure_relationship_types),
    ]
