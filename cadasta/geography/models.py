from django.contrib.gis.db import models


class WorldBorder(models.Model):
    name = models.CharField(max_length=50)
    pop_est = models.IntegerField('Population estimate')
    fips = models.CharField('FIPS Code', max_length=3)
    iso2 = models.CharField('2 Digit ISO', max_length=5)
    iso3 = models.CharField('3 Digit ISO', max_length=3)
    un = models.IntegerField('United Nations Code')
    region = models.CharField('Region Code', max_length=23)
    subregion = models.CharField('Sub-Region Code', max_length=25)
    mpoly = models.MultiPolygonField()

    def __str__(self):
        return self.name
