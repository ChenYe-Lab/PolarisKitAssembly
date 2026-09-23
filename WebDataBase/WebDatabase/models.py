# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.utils import timezone
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class DeduplicatingCreateManager(models.Manager):
    def create(self, **kwargs):
        instance = self.model(**kwargs)
        instance.save(force_insert=True, using=self._db)
        return instance


class DeduplicatingSaveMixin(models.Model):
    objects = DeduplicatingCreateManager()

    class Meta:
        abstract = True

    def _dedup_lookup(self):
        lookup = {}
        for field in self._meta.concrete_fields:
            if field.primary_key:
                continue
            lookup[field.attname] = getattr(self, field.attname)
        return lookup

    def save(self, *args, **kwargs):
        using = kwargs.get("using") or self._state.db
        duplicate_qs = type(self).objects.using(using).filter(**self._dedup_lookup())
        if self.pk is not None:
            duplicate_qs = duplicate_qs.exclude(pk=self.pk)

        duplicate = duplicate_qs.first()
        if duplicate is not None:
            setattr(self, self._meta.pk.attname, duplicate.pk)
            self._state.adding = False
            self._state.db = using
            return

        super().save(*args, **kwargs)


class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=150)

    class Meta:
        managed = False
        db_table = 'auth_group'


class AuthGroupPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)


class AuthPermission(models.Model):
    name = models.CharField(max_length=255)
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)


class AuthUser(models.Model):
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.IntegerField()
    username = models.CharField(unique=True, max_length=150)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.CharField(max_length=254)
    is_staff = models.IntegerField()
    is_active = models.IntegerField()
    date_joined = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'auth_user'


class AuthUserGroups(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_groups'
        unique_together = (('user', 'group'),)


class AuthUserUserPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_user_permissions'
        unique_together = (('user', 'permission'),)


class Backbone_Culture_Functions(DeduplicatingSaveMixin, models.Model):
    bcfid = models.AutoField(primary_key=True)
    backbone_id = models.ForeignKey('Backbonetable', models.CASCADE, db_column='backbone_id')
    function_content = models.CharField(max_length=50)
    function_type = models.CharField(max_length=50)

    class Meta:
        managed = True
        db_table = 'backbone_culture_functions'


class Backbonescartable(DeduplicatingSaveMixin, models.Model):
    backbonescarid = models.AutoField(db_column='BackboneScarID', primary_key=True)  # Field name made lowercase.
    backboneid = models.ForeignKey('Backbonetable', models.CASCADE, db_column='BackboneID')  # Field name made lowercase.
    bsmbi = models.CharField(db_column='BsmBI', max_length=100)  # Field name made lowercase.
    bsai = models.CharField(db_column='BsaI', max_length=100)  # Field name made lowercase.
    bbsi = models.CharField(db_column='BbsI', max_length=100)  # Field name made lowercase.
    aari = models.CharField(db_column='AarI', max_length=100)  # Field name made lowercase.
    sapi = models.CharField(db_column='SapI', max_length=100)  # Field name made lowercase.

    class Meta:
        managed = True
        db_table = 'backbonescartable'


class Backbonetable(models.Model):
    id = models.AutoField(db_column='ID', primary_key=True)  # Field name made lowercase.
    name = models.CharField(db_column='Name', max_length=20)  # Field name made lowercase.
    length = models.IntegerField(db_column='Length', blank=True, null=True)  # Field name made lowercase.
    sequence = models.TextField(db_column='Sequence')  # Field name made lowercase.
    # ori = models.CharField(db_column='Ori', max_length=20)  # Field name made lowercase.
    # marker = models.CharField(db_column='Marker', max_length=20)  # Field name made lowercase.
    species = models.CharField(db_column='Species', max_length=50, blank=True, null=True)  # Field name made lowercase.
    copynumber = models.CharField(db_column='CopyNumber', max_length=20, blank=True, null=True)  # Field name made lowercase.
    notes = models.TextField(db_column='Notes', blank=True, null=True)  # Field name made lowercase.
    alias = models.CharField(db_column='Alias', max_length=500, blank=True, null=True)  # Field name made lowercase.
    user = models.CharField(db_column='User', max_length=50)  # Field name made lowercase.
    tag = models.CharField(max_length=50, blank=True, null=True)
    updatedate = models.DateTimeField(blank=True, null=True)
    uploaddate = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'backbonetable'


class Dbdtable(models.Model):
    id = models.AutoField(db_column='ID', primary_key=True)  # Field name made lowercase.
    name = models.CharField(db_column='Name', max_length=20)  # Field name made lowercase.
    i0 = models.FloatField(db_column='I0')  # Field name made lowercase.
    kd = models.FloatField()

    class Meta:
        managed = True
        db_table = 'dbdtable'


class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.PositiveSmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'django_admin_log'


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoMigrations(models.Model):
    id = models.BigAutoField(primary_key=True)
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'


class Gates(models.Model):
    collection = models.CharField(max_length=100, blank=True, null=True)
    name = models.CharField(max_length=100, blank=True, null=True)
    system = models.CharField(max_length=100, blank=True, null=True)
    group = models.CharField(max_length=100, blank=True, null=True)
    regulator = models.CharField(max_length=100, blank=True, null=True)
    gate_type = models.CharField(max_length=100, blank=True, null=True)
    color = models.CharField(max_length=100, blank=True, null=True)
    model = models.CharField(max_length=100, blank=True, null=True)
    structure = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'gates'


class Gatetabletest(models.Model):
    gateid = models.IntegerField(db_column='GateID', blank=True, null=True)  # Field name made lowercase.
    gatename = models.CharField(db_column='GateName', max_length=100, blank=True, null=True)  # Field name made lowercase.
    gatetype = models.CharField(db_column='GateType', max_length=100, blank=True, null=True)  # Field name made lowercase.
    responsefunction = models.CharField(db_column='ResponseFunction', max_length=100, blank=True, null=True)  # Field name made lowercase.
    parameter1 = models.FloatField(db_column='Parameter1', blank=True, null=True)  # Field name made lowercase.
    parameter2 = models.FloatField(db_column='Parameter2', blank=True, null=True)  # Field name made lowercase.
    parameter3 = models.FloatField(db_column='Parameter3', blank=True, null=True)  # Field name made lowercase.
    parameter4 = models.FloatField(db_column='Parameter4', blank=True, null=True)  # Field name made lowercase.
    xmin = models.FloatField(db_column='Xmin', blank=True, null=True)  # Field name made lowercase.
    xmax = models.FloatField(db_column='Xmax', blank=True, null=True)  # Field name made lowercase.
    gatepromoterid = models.IntegerField(db_column='GatePromoterID', blank=True, null=True)  # Field name made lowercase.
    gaterbsid = models.IntegerField(db_column='GateRBSID', blank=True, null=True)  # Field name made lowercase.
    gatecdsid = models.IntegerField(db_column='GateCDSID', blank=True, null=True)  # Field name made lowercase.
    gateterminatorid = models.IntegerField(db_column='GateTerminatorID', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'gatetabletest'





class Gbptest(models.Model):
    index = models.BigIntegerField(blank=True, null=True)
    partid = models.BigIntegerField(db_column='PartID', blank=True, null=True)  # Field name made lowercase.
    alias = models.TextField(blank=True, null=True)
    up = models.TextField(db_column='UP', blank=True, null=True)  # Field name made lowercase.
    co_35 = models.TextField(blank=True, null=True)
    spacer = models.TextField(blank=True, null=True)
    ext_10 = models.TextField(blank=True, null=True)
    co_10 = models.TextField(blank=True, null=True)
    disc = models.TextField(blank=True, null=True)
    utr = models.TextField(db_column='UTR', blank=True, null=True)  # Field name made lowercase.
    note = models.TextField(db_column='Note', blank=True, null=True)  # Field name made lowercase.
    rpu11 = models.FloatField(db_column='RPU11', blank=True, null=True)  # Field name made lowercase.
    rpu12 = models.FloatField(db_column='RPU12', blank=True, null=True)  # Field name made lowercase.
    rpu13 = models.FloatField(db_column='RPU13', blank=True, null=True)  # Field name made lowercase.
    aveg1 = models.FloatField(db_column='Aveg1', blank=True, null=True)  # Field name made lowercase.
    rawdatafile1 = models.TextField(db_column='RawDataFile1', blank=True, null=True)  # Field name made lowercase.
    rpu21 = models.FloatField(db_column='RPU21', blank=True, null=True)  # Field name made lowercase.
    rpu22 = models.FloatField(db_column='RPU22', blank=True, null=True)  # Field name made lowercase.
    rpu23 = models.FloatField(db_column='RPU23', blank=True, null=True)  # Field name made lowercase.
    aveg2 = models.FloatField(db_column='Aveg2', blank=True, null=True)  # Field name made lowercase.
    rawdatafile2 = models.TextField(db_column='RawDataFile2', blank=True, null=True)  # Field name made lowercase.
    unnamed_20 = models.FloatField(db_column='Unnamed: 20', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    unnamed_21 = models.FloatField(db_column='Unnamed: 21', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    unnamed_22 = models.FloatField(db_column='Unnamed: 22', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    unnamed_23 = models.FloatField(db_column='Unnamed: 23', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    unnamed_24 = models.FloatField(db_column='Unnamed: 24', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.

    class Meta:
        managed = False
        db_table = 'gbptest'


class Gubangpromoterlibrary(models.Model):
    partid = models.IntegerField(db_column='PartID', blank=True, null=True)  # Field name made lowercase.
    alias = models.CharField(max_length=100, blank=True, null=True)
    up = models.CharField(db_column='UP', max_length=100, blank=True, null=True)  # Field name made lowercase.
    co_35 = models.CharField(db_column='co_-35', max_length=100, blank=True, null=True)  # Field renamed to remove unsuitable characters.
    spacer = models.CharField(max_length=100, blank=True, null=True)
    ext_10 = models.CharField(db_column='ext-10', max_length=100, blank=True, null=True)  # Field renamed to remove unsuitable characters.
    co_10 = models.CharField(db_column='co_-10', max_length=100, blank=True, null=True)  # Field renamed to remove unsuitable characters.
    disc = models.CharField(max_length=100, blank=True, null=True)
    utr = models.CharField(db_column='UTR', max_length=100, blank=True, null=True)  # Field name made lowercase.
    note = models.CharField(db_column='Note', max_length=100, blank=True, null=True)  # Field name made lowercase.
    tset1_rpu1 = models.FloatField(db_column='tset1_RPU1', blank=True, null=True)  # Field name made lowercase.
    test1_rpu2 = models.FloatField(db_column='test1_RPU2', blank=True, null=True)  # Field name made lowercase.
    test1_rpu3 = models.FloatField(db_column='test1_RPU3', blank=True, null=True)  # Field name made lowercase.
    test1_aveg = models.FloatField(db_column='test1_Aveg', blank=True, null=True)  # Field name made lowercase.
    test1_rawdatafile = models.CharField(db_column='test1_RawDataFile', max_length=100, blank=True, null=True)  # Field name made lowercase.
    test2_rpu1 = models.FloatField(db_column='test2_RPU1', blank=True, null=True)  # Field name made lowercase.
    test2_rpu2 = models.FloatField(db_column='test2_RPU2', blank=True, null=True)  # Field name made lowercase.
    test2_rpu3 = models.FloatField(db_column='test2_RPU3', blank=True, null=True)  # Field name made lowercase.
    test2_aveg = models.FloatField(db_column='test2_Aveg', blank=True, null=True)  # Field name made lowercase.
    test2_rawdatafile = models.CharField(db_column='test2_RawDataFile', max_length=100, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'gubangpromoterlibrary'




class Lbddimertable(models.Model):
    id = models.AutoField(db_column='ID', primary_key=True)  # Field name made lowercase.
    name = models.CharField(db_column='Name', max_length=20)  # Field name made lowercase.
    k1 = models.FloatField()
    k2 = models.FloatField()
    k3 = models.FloatField()
    i = models.FloatField(db_column='I')  # Field name made lowercase.

    class Meta:
        managed = True
        db_table = 'lbddimertable'


class Lbdnrtable(models.Model):
    id = models.AutoField(db_column='ID', primary_key=True)  # Field name made lowercase.
    name = models.CharField(db_column='Name', max_length=20)  # Field name made lowercase.
    k1 = models.FloatField()
    k2 = models.FloatField()
    k3 = models.FloatField()
    kx1 = models.FloatField()
    kx2 = models.FloatField()

    class Meta:
        managed = True
        db_table = 'lbdnrtable'


class Parentbackbonetable(models.Model):
    pbid = models.AutoField(primary_key=True)
    sonplasmidid = models.ForeignKey('Plasmidneed', models.DO_NOTHING, db_column='sonplasmidid')
    parentbackboneid = models.ForeignKey(Backbonetable, models.DO_NOTHING, db_column='parentbackboneid')

    class Meta:
        managed = True
        db_table = 'parentbackbonetable'


class Parentparttable(models.Model):
    ppid = models.AutoField(primary_key=True)
    sonplasmidid = models.ForeignKey('Plasmidneed', models.DO_NOTHING, db_column='sonplasmidid')
    parentpartid = models.ForeignKey('Parttable', models.DO_NOTHING, db_column='parentpartid')

    class Meta:
        managed = True
        db_table = 'parentparttable'


class Parentplasmidtable(models.Model):
    ppid = models.AutoField(db_column='PPID', primary_key=True)  # Field name made lowercase.
    sonplasmidid = models.ForeignKey('Plasmidneed', models.DO_NOTHING, db_column='SonPlasmidID')  # Field name made lowercase.
    parentplasmidid = models.ForeignKey('Plasmidneed', models.DO_NOTHING, db_column='ParentPlasmidID', related_name='parentplasmidtable_parentplasmidid_set')  # Field name made lowercase.

    class Meta:
        managed = True
        db_table = 'parentplasmidtable'


class Partrputable(models.Model):
    prid = models.AutoField(db_column='PRID', primary_key=True)  # Field name made lowercase.
    partid = models.ForeignKey('Parttable', models.DO_NOTHING, db_column='PartID')  # Field name made lowercase.
    rpu = models.FloatField(db_column='RPU')  # Field name made lowercase.
    teststrain = models.CharField(db_column='TestStrain', max_length=50, blank=True, null=True)  # Field name made lowercase.
    note = models.CharField(db_column='Note', max_length=100, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = True
        db_table = 'partrputable'


class Parts(models.Model):
    collection = models.CharField(max_length=100, blank=True, null=True)
    type = models.CharField(max_length=100, blank=True, null=True)
    name = models.CharField(max_length=100, blank=True, null=True)
    dnasequence = models.CharField(max_length=100, blank=True, null=True)
    parameters = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'parts'


class Partscartable(DeduplicatingSaveMixin, models.Model):
    partscarid = models.AutoField(db_column='PartScarID', primary_key=True)  # Field name made lowercase.
    part_id = models.ForeignKey('Parttable',models.CASCADE,db_column='part_id')
    bsmbi = models.CharField(db_column='BsmBI', max_length=100)  # Field name made lowercase.
    bsai = models.CharField(db_column='BsaI', max_length=100)  # Field name made lowercase.
    bbsi = models.CharField(db_column='BbsI', max_length=100)  # Field name made lowercase.
    aari = models.CharField(db_column='AarI', max_length=100)  # Field name made lowercase.
    sapi = models.CharField(db_column='SapI', max_length=100)  # Field name made lowercase.

    class Meta:
        managed = True
        db_table = 'partscartable'


class Parttable(models.Model):
    partid = models.AutoField(db_column='PartID', primary_key=True)  # Field name made lowercase.
    name = models.CharField(db_column='Name', max_length=100, blank=True, null=True)  # Field name made lowercase.
    alias = models.CharField(db_column='Alias', max_length=100, blank=True, null=True)  # Field name made lowercase.
    lengthinlevel0 = models.IntegerField(db_column='LengthInLevel0')  # Field name made lowercase.
    level0sequence = models.TextField(db_column='Level0Sequence', blank=True, null=True)  # Field name made lowercase.
    confirmedsequence = models.TextField(db_column='ConfirmedSequence', blank=True, null=True)  # Field name made lowercase.
    insertsequence = models.TextField(db_column='InsertSequence', blank=True, null=True)  # Field name made lowercase.
    sourceorganism = models.TextField(db_column='SourceOrganism', blank=True, null=True)  # Field name made lowercase.
    reference = models.TextField(db_column='Reference', blank=True, null=True)  # Field name made lowercase.
    note = models.TextField(db_column='Note', blank=True, null=True)  # Field name made lowercase.
    type = models.IntegerField(db_column='Type')  # Field name made lowercase.
    user = models.CharField(db_column='User', max_length=50, blank=True, null=True)  # Field name made lowercase.
    tag = models.CharField(max_length=50, blank=True, null=True)
    uploaddate = models.DateTimeField(blank=True, null=True)
    updatedate = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'parttable'


class Plasmid_Culture_Functions(DeduplicatingSaveMixin, models.Model):
    pcfid = models.AutoField(primary_key=True)
    plasmid_id = models.ForeignKey('Plasmidneed', models.DO_NOTHING,db_column="plasmid_id")
    function_content = models.CharField(max_length=100)
    function_type = models.CharField(max_length=100)

    class Meta:
        managed = True
        db_table = 'plasmid_culture_functions'


class Plasmidneed(models.Model):
    plasmidid = models.AutoField(db_column='PlasmidID', primary_key=True)  # Field name made lowercase.
    name = models.CharField(db_column='Name', max_length=20, blank=True, null=True)  # Field name made lowercase.
    # oricloning = models.CharField(db_column='OriCloning', max_length=20)  # Field name made lowercase.
    # orihost = models.CharField(db_column='OriHost', max_length=20)  # Field name made lowercase.
    # markercloning = models.CharField(db_column='MarkerCloning', max_length=20)  # Field name made lowercase.
    # markerhost = models.CharField(db_column='MarkerHost', max_length=20)  # Field name made lowercase.
    level = models.CharField(db_column='Level', max_length=10)  # Field name made lowercase.
    length = models.IntegerField(db_column='Length')  # Field name made lowercase.
    sequenceconfirm = models.TextField(db_column='SequenceConfirm')  # Field name made lowercase.
    plate = models.CharField(db_column='Plate', max_length=100, blank=True, null=True)  # Field name made lowercase.
    state = models.IntegerField(db_column='State', blank=True, null=True)  # Field name made lowercase.
    user = models.CharField(db_column='User', max_length=20)  # Field name made lowercase.
    note = models.CharField(db_column='Note', max_length=500, blank=True, null=True)  # Field name made lowercase.
    alias = models.CharField(db_column='Alias', max_length=500, blank=True, null=True)  # Field name made lowercase.
    customparentinformation = models.TextField(db_column='CustomParentInformation', blank=True, null=True)  # Field name made lowercase.
    tag = models.CharField(max_length=50, blank=True, null=True)
    uploaddate = models.DateTimeField(blank=True, null=True)
    updatedate = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'plasmidneed'


class Plasmidscartable(DeduplicatingSaveMixin, models.Model):
    plasmidscarid = models.AutoField(db_column='PlasmidScarID', primary_key=True)  # Field name made lowercase.
    plasmidid = models.ForeignKey(Plasmidneed, models.CASCADE, db_column='PlasmidID')  # Field name made lowercase.
    bsmbi = models.CharField(db_column='BsmBI', max_length=100)  # Field name made lowercase.
    bsai = models.CharField(db_column='BsaI', max_length=100)  # Field name made lowercase.
    bbsi = models.CharField(db_column='BbsI', max_length=100)  # Field name made lowercase.
    aari = models.CharField(db_column='AarI', max_length=100)  # Field name made lowercase.
    sapi = models.CharField(db_column='SapI', max_length=100)  # Field name made lowercase.

    class Meta:
        managed = True
        db_table = 'plasmidscartable'


class Plasmidunessential(models.Model):
    id = models.AutoField(db_column='ID', primary_key=True)  # Field name made lowercase.
    plasmidid = models.ForeignKey(Plasmidneed, models.DO_NOTHING, db_column='PlasmidID')  # Field name made lowercase.
    alias = models.CharField(db_column='Alias', max_length=20, blank=True, null=True)  # Field name made lowercase.
    avaliable = models.IntegerField(db_column='Avaliable', blank=True, null=True)  # Field name made lowercase.
    function = models.TextField(db_column='Function', blank=True, null=True)  # Field name made lowercase.
    reference = models.TextField(db_column='Reference', blank=True, null=True)  # Field name made lowercase.
    sourceorganism = models.TextField(db_column='SourceOrganism', blank=True, null=True)  # Field name made lowercase.
    comment = models.TextField(db_column='Comment', blank=True, null=True)  # Field name made lowercase.
    seqfileaddress = models.TextField(db_column='SeqFileAddress', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'plasmidunessential'


class Straintable(models.Model):
    strainid = models.AutoField(db_column='StrainID', primary_key=True)  # Field name made lowercase.
    strainname = models.CharField(db_column='StrainName', max_length=20)  # Field name made lowercase.
    background = models.CharField(db_column='Background', max_length=20)  # Field name made lowercase.
    marker = models.CharField(db_column='Marker', max_length=30)  # Field name made lowercase.
    store = models.CharField(db_column='Store', max_length=100)  # Field name made lowercase.

    class Meta:
        managed = True
        db_table = 'straintable'
        

class StrainGenotypeTable(models.Model):
    sgid = models.AutoField(db_column='sdid',primary_key=True)
    plasmidid = models.ForeignKey(Plasmidneed,models.CASCADE,db_column='plasmidid')
    strainid = models.ForeignKey(Straintable,models.CASCADE,db_column='strainid')

    class Meta:
        managed = True
        db_table = 'strain_genotype_table'
    

class Structures(models.Model):
    collection = models.CharField(max_length=100, blank=True, null=True)
    name = models.CharField(max_length=100, blank=True, null=True)
    inputs = models.CharField(max_length=100, blank=True, null=True)
    outputs = models.CharField(max_length=100, blank=True, null=True)
    devices = models.CharField(max_length=500, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'structures'


class TbBackboneUserfileaddress(models.Model):
    ufid = models.AutoField(primary_key=True)
    userid = models.ForeignKey('User', models.DO_NOTHING, db_column='userid', blank=True, null=True)
    backboneid = models.ForeignKey(Backbonetable, models.DO_NOTHING, db_column='backboneid', blank=True, null=True)
    fileaddress = models.TextField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'tb_backbone_userfileaddress'


class TbPartUserfileaddress(models.Model):
    ufid = models.AutoField(primary_key=True)
    userid = models.ForeignKey('User', models.DO_NOTHING, db_column='userid', blank=True, null=True)
    partid = models.ForeignKey(Parttable, models.DO_NOTHING, db_column='partid', blank=True, null=True)
    fileaddress = models.TextField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'tb_part_userfileaddress'


class TbPlasmidUserfileaddress(models.Model):
    ufid = models.AutoField(primary_key=True)
    userid = models.ForeignKey('User', models.DO_NOTHING, db_column='userid', blank=True, null=True)
    plasmidid = models.ForeignKey(Plasmidneed, models.DO_NOTHING, db_column='plasmidid', blank=True, null=True)
    fileaddress = models.TextField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'tb_plasmid_userfileaddress'


class Temporaryrepository(models.Model):
    id = models.CharField(primary_key=True, max_length=32)
    userid = models.ForeignKey('CustomUser', models.DO_NOTHING, db_column='userid')
    repositorycreate_time = models.DateTimeField(blank=True, null=True)
    repositoryupdate_time = models.DateTimeField(blank=True, null=True)
    repositoryexpire_time = models.DateTimeField(blank=True, null=True)
    data = models.JSONField(blank=True, null=True)
    name = models.CharField(max_length=500, blank=True, null=True)
    note = models.TextField(db_column='Note', blank=True, null=True)  # Field name made lowercase.
    alias = models.CharField(db_column = 'alias',max_length=100, blank=True, null = True)
    level = models.IntegerField(db_column='Level',blank=True, null = True)
    part_start_scar = models.CharField(db_column='part_start_scar',max_length=10,blank=True, null=True)
    part_end_scar = models.CharField(db_column='part_end_scar',max_length=10,blank=True,null=True)
    
    class Meta:
        managed = True
        db_table = 'temporaryrepository'
    def is_expired(self):
        print("is_expired")
        return timezone.now() > self.repositoryexpire_time


class Testdatatable(models.Model):
    testdataid = models.AutoField(db_column='TestDataID', primary_key=True)  # Field name made lowercase.
    testdataname = models.CharField(db_column='TestDataName', max_length=20)  # Field name made lowercase.
    purpose = models.TextField(db_column='Purpose', blank=True, null=True)  # Field name made lowercase.
    standardstrain = models.CharField(db_column='StandardStrain', max_length=30, blank=True, null=True)  # Field name made lowercase.
    positivecontrol = models.CharField(db_column='PositiveControl', max_length=100, blank=True, null=True)  # Field name made lowercase.
    dataaddress = models.TextField(db_column='DataAddress', blank=True, null=True)  # Field name made lowercase.
    date = models.TextField(db_column='Date', blank=True, null=True)  # Field name made lowercase.
    strain = models.CharField(db_column='Strain', max_length=100)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'testdatatable'

class UserManager(BaseUserManager):
    def create_user(self,uname, email, password, **extra_fields):
        """创建普通用户"""
        print(uname)
        print(email)
        print(password)
        extra_fields.setdefault('is_staff',True)
        extra_fields.setdefault('is_active',True)
        if not email or not uname:
            raise ValueError(_('用户名和邮箱必须提供'))
        email = self.normalize_email(email)
        user = self.model(email = email, uname = uname,username = uname, **extra_fields)
        user.set_password(password)
        print(user)
        user.save(using = self._db)
        return user
    def create_superuser(self, uname, email, password = None, **extra_fields):
        """创建超级用户"""
        extra_fields.setdefault('is_staff',True)
        extra_fields.setdefault('is_superuser',True)
        extra_fields.setdefault('is_active',True)
        
        if(extra_fields.get('is_staff') is not True):
            raise ValueError(_('用户必须有 is_staff=True'))
        if(extra_fields.get('is_superuser') is not True):
            raise ValueError(_('超级用户必须有 is_superuser=True'))
        return self.create_user(uname, email,password,**extra_fields)
    
        
    
class User(models.Model):
    uid = models.AutoField(primary_key=True)
    uname = models.CharField(max_length=50)
    email = models.CharField(max_length=50, blank=True, null=True)
    create_time = models.DateField(blank=True, null=True)
    password = models.CharField(max_length=50)

    class Meta:
        managed = True
        db_table = 'user'

class CustomUser(AbstractUser):
    
    class UserRole(models.TextChoices):
        USER = 'user',_("普通用户")
        EDITOR = 'editor',_('编辑者')
        MANAGER = 'manager',_('管理员')
        ADMIN = 'admin',_('超级管理员')
    
    uid = models.AutoField(primary_key=True)
    uname = models.CharField(max_length=50)
    
    role = models.CharField(
        max_length=20,
        choices = UserRole.choices,
        default = UserRole.USER
    )
    
    email = models.CharField(max_length=50, blank=True, null=True)
    is_email_verified = models.BooleanField(default=False)
    objects = UserManager()
    last_activate = models.DateTimeField(auto_now=True)
    create_time = models.DateField(blank=True, null=True)
    
    password = models.CharField(max_length=500,null=False,default="f06a53bb5da60c512506097e48203d4c")

    class Meta:
        managed = True
        db_table = "CustomUser"
        verbose_name = _('用户')
        verbose_name_plural = _('用户')

    
    def __str__(self):
        return f"{self.uname} ({self.get_role_display()})"
    
    @property
    def is_editor(self):
        """是否是编辑"""
        return self.role in [self.UserRole.EDITOR, self.UserRole.MANAGER, self.UserRole.ADMIN]
    
    @property
    def is_manager(self):
        """是否是管理员"""
        return self.role in [self.UserRole.MANAGER, self.UserRole.ADMIN]
    
    @property
    def is_admin(self):
        """是否是超级管理员"""
        return self.role == self.UserRole.ADMIN

        
# class CustomUser(AbstractUser):
#     uid = models.AutoField(primary_key=True)
#     uname = models.CharField(max_length=50)
    
#     email = models.CharField(max_length=50, blank=True, null=True)
#     avatar = models.ImageField(_("头像"),upload_to='avatars/',blank=True, null=True)
    
#     create_time = models.DateField(blank=True, null=True)
#     password = models.CharField(max_length=50)
    
#     class Meta:
#         verbose_name = _('用户')
#         verbose_name_plural = _('用户')
#     def __str__(self):
#         return self.username
    
class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete = models.CASCADE,
        related_name='profile',
        verbose_name=_('用户')
    )
    
    show_email = models.BooleanField(_('公开邮箱'),default = False)
    show_phone = models.BooleanField(_('公开手机号'),default = False)
    
    create_at = models.DateTimeField(_('创建时间'), auto_now_add=True)

    class Meta:
        verbose_name = _('用户资料')
        verbose_name_plural = _('用户资料')
    def __str__(self):
        return f"{self.user.uname} 的资料"
    
    @classmethod
    def get_or_create_profile(cls, user):
        profile, created = cls.objects.get_or_create(user = user)
        return profile


class VisitorProfile(models.Model):
    id = models.BigAutoField(primary_key=True)
    visitor_uuid = models.CharField(max_length=36, unique=True)
    institution = models.CharField(max_length=255)
    lab_name = models.CharField(max_length=255)
    person_name = models.CharField(max_length=255)
    cookie_key = models.CharField(max_length=128, unique=True, blank=True, null=True)
    visit_count = models.PositiveIntegerField(default=0)
    first_seen_at = models.DateTimeField(default=timezone.now)
    last_seen_at = models.DateTimeField(default=timezone.now)
    last_path = models.CharField(max_length=255, blank=True, null=True)
    last_ip = models.CharField(max_length=45, blank=True, null=True)
    last_user_agent = models.CharField(max_length=512, blank=True, null=True)
    created_by_user = models.ForeignKey(
        'CustomUser',
        models.SET_NULL,
        db_column='created_by_user_id',
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = True
        db_table = 'visitorprofile'

    def __str__(self):
        return f"{self.person_name} ({self.institution}/{self.lab_name})"


class VisitorAccessLog(models.Model):
    id = models.BigAutoField(primary_key=True)
    visitor = models.ForeignKey(VisitorProfile, models.CASCADE, db_column='visitor_id')
    visited_at = models.DateTimeField(default=timezone.now)
    path = models.CharField(max_length=255)
    method = models.CharField(max_length=16, default='GET')
    ip = models.CharField(max_length=45, blank=True, null=True)
    user_agent = models.CharField(max_length=512, blank=True, null=True)
    referer = models.CharField(max_length=512, blank=True, null=True)
    cookie_snapshot = models.JSONField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'visitoraccesslog'

    def __str__(self):
        return f"{self.visitor_id} {self.method} {self.path}"


class VisitorFeedback(models.Model):
    FEEDBACK_TYPE_ISSUE = "issue"
    FEEDBACK_TYPE_SUGGESTION = "suggestion"
    FEEDBACK_TYPE_CHOICES = [
        (FEEDBACK_TYPE_ISSUE, "Issue"),
        (FEEDBACK_TYPE_SUGGESTION, "Suggestion"),
    ]

    STATUS_PENDING = "pending"
    STATUS_REVIEWED = "reviewed"
    STATUS_RESOLVED = "resolved"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_REVIEWED, "Reviewed"),
        (STATUS_RESOLVED, "Resolved"),
    ]

    visitor_profile = models.ForeignKey(
        VisitorProfile,
        on_delete=models.CASCADE,
        db_column='visitor_id'
    )
    feedback_type = models.CharField(max_length=32, choices=FEEDBACK_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    content = models.TextField()
    contact_email = models.EmailField(blank=True)
    page_path = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = True
        db_table = 'visitorfeedback'

    def __str__(self):
        return f"{self.get_feedback_type_display()}: {self.title}"

class Yeastmodels(models.Model):
    collection = models.CharField(max_length=100, blank=True, null=True)
    name = models.CharField(max_length=100, blank=True, null=True)
    function1 = models.CharField(max_length=100, blank=True, null=True)
    function2 = models.CharField(max_length=100, blank=True, null=True)
    toxicity = models.CharField(max_length=100, blank=True, null=True)
    cytometry = models.CharField(max_length=100, blank=True, null=True)
    ymax = models.FloatField(blank=True, null=True)
    ymin = models.FloatField(blank=True, null=True)
    k_value = models.FloatField(blank=True, null=True)
    n_value = models.FloatField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'yeastmodels'


class Yeastparts(models.Model):
    name = models.CharField(max_length=100, blank=True, null=True)
    type = models.CharField(max_length=100, blank=True, null=True)
    dnasequence = models.CharField(max_length=100, blank=True, null=True)
    strength = models.FloatField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'yeastparts'


class Backbonefeaturetable(DeduplicatingSaveMixin, models.Model):
    bfif = models.AutoField(primary_key=True)
    backboneid = models.ForeignKey('Backbonetable', models.CASCADE, db_column='backboneid')
    feature_start = models.IntegerField()
    feature_end = models.IntegerField()
    feature_type = models.CharField(max_length=50)
    feature_label = models.CharField(max_length=50)
    feature_color = models.CharField(max_length=50)
    feature_apeinfo = models.CharField(max_length=50)

    strand = models.SmallIntegerField(null=True, blank=True)
    feature_group = models.CharField(max_length=64, blank=True, default='')
    segment_order = models.PositiveIntegerField(default=0)
    location_operator = models.CharField(max_length=20, blank=True, default='')
    coordinate_system = models.CharField(max_length=30, default='one_based_closed')
    feature_metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        managed = True
        db_table = 'BackboneFeatureTable'


class Partfeaturetable(DeduplicatingSaveMixin, models.Model):
    pfid = models.AutoField(primary_key=True)
    partid = models.ForeignKey('Parttable', models.CASCADE, db_column='partid')
    feature_start = models.IntegerField()
    feature_end = models.IntegerField()
    feature_type = models.CharField(max_length=50)
    feature_label = models.CharField(max_length=50)
    feature_color = models.CharField(max_length=50)
    feature_apeinfo = models.CharField(max_length=50)

    strand = models.SmallIntegerField(null=True, blank=True)
    feature_group = models.CharField(max_length=64, blank=True, default='')
    segment_order = models.PositiveIntegerField(default=0)
    location_operator = models.CharField(max_length=20, blank=True, default='')
    coordinate_system = models.CharField(max_length=30, default='one_based_closed')
    feature_metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        managed = True
        db_table = 'PartFeatureTable'


class Plasmidfeaturetable(DeduplicatingSaveMixin, models.Model):
    pfid = models.AutoField(primary_key=True)
    plasmidid = models.ForeignKey('Plasmidneed', models.CASCADE, db_column='plasmidid')
    feature_start = models.IntegerField()
    feature_end = models.IntegerField()
    feature_type = models.CharField(max_length=50)
    feature_label = models.CharField(max_length=50)
    feature_color = models.CharField(max_length=50)
    feature_apeinfo = models.CharField(max_length=50)

    strand = models.SmallIntegerField(null=True, blank=True)
    feature_group = models.CharField(max_length=64, blank=True, default='')
    segment_order = models.PositiveIntegerField(default=0)
    location_operator = models.CharField(max_length=20, blank=True, default='')
    coordinate_system = models.CharField(max_length=30, default='one_based_closed')
    feature_metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        managed = True
        db_table = 'PlasmidFeatureTable'
