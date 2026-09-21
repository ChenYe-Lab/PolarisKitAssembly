# 数据库结构说明

## 文档范围

- 项目技术栈：Django 3.2 + MySQL。
- 当前主业务模型来源：`WebDataWorld/WebDatabase/models.py`。
- 历史自动反射模型来源：`WebDataWorld/models.py`，仅在当前主模型中不存在时作为兼容补充说明。
- 当前登录用户主模型：`WebDatabase.CustomUser`。

## 总体结构概览

- `CustomUser` 是当前用户主表，`UserProfile` 为其一对一扩展信息表。
- `VisitorProfile`、`VisitorAccessLog`、`VisitorFeedback` 组成访客信息、访问日志和反馈管理结构。
- `Backbonetable`、`Parttable`、`Plasmidneed` 是生物元件与质粒组装的核心主表。
- `Parentbackbonetable`、`Parentparttable`、`Parentplasmidtable` 用于表达装配过程中的父子关系。
- `Backbonefeaturetable`、`Partfeaturetable`、`Plasmidfeaturetable` 用于存储序列 feature 标注信息。
- `auth_*` 和 `django_*` 是 Django 框架自带的权限、会话、迁移、日志相关表。

## 常见字段类型说明

- `AutoField / BigAutoField`：自增整型主键，常用于业务表或系统表主键。
- `CharField`：短字符串类型，需关注 max_length 限制。
- `TextField`：长文本类型，适合序列、备注、路径等大字段。
- `IntegerField / PositiveIntegerField / PositiveSmallIntegerField`：整数类型；Positive 系列不应为负数。
- `FloatField`：浮点数类型，用于实验参数、强度、阈值等数值字段。
- `BooleanField`：布尔值，表示是/否状态。
- `DateField`：仅存储日期。
- `DateTimeField`：存储日期与时间；auto_now / auto_now_add 表示自动写入时间。
- `EmailField`：带邮箱格式校验的字符串。
- `JSONField`：存储 JSON 结构化数据。
- `ForeignKey`：多对一关系，当前表保存关联表主键。
- `OneToOneField`：一对一关系，常用于主表的扩展信息。

## 当前生效的表关系

- `auth_group_permissions.group` -> `AuthGroup`（ForeignKey，删除策略 `models.DO_NOTHING`）
- `auth_group_permissions.permission` -> `AuthPermission`（ForeignKey，删除策略 `models.DO_NOTHING`）
- `auth_permission.content_type` -> `DjangoContentType`（ForeignKey，删除策略 `models.DO_NOTHING`）
- `auth_user_groups.user` -> `AuthUser`（ForeignKey，删除策略 `models.DO_NOTHING`）
- `auth_user_groups.group` -> `AuthGroup`（ForeignKey，删除策略 `models.DO_NOTHING`）
- `auth_user_user_permissions.user` -> `AuthUser`（ForeignKey，删除策略 `models.DO_NOTHING`）
- `auth_user_user_permissions.permission` -> `AuthPermission`（ForeignKey，删除策略 `models.DO_NOTHING`）
- `backbone_culture_functions.backbone_id` -> `Backbonetable`（ForeignKey，删除策略 `models.CASCADE`）
- `backbonescartable.BackboneID` -> `Backbonetable`（ForeignKey，删除策略 `models.CASCADE`）
- `django_admin_log.content_type` -> `DjangoContentType`（ForeignKey，删除策略 `models.DO_NOTHING`）
- `django_admin_log.user` -> `AuthUser`（ForeignKey，删除策略 `models.DO_NOTHING`）
- `parentbackbonetable.sonplasmidid` -> `Plasmidneed`（ForeignKey，删除策略 `models.DO_NOTHING`）
- `parentbackbonetable.parentbackboneid` -> `Backbonetable`（ForeignKey，删除策略 `models.DO_NOTHING`）
- `parentparttable.sonplasmidid` -> `Plasmidneed`（ForeignKey，删除策略 `models.DO_NOTHING`）
- `parentparttable.parentpartid` -> `Parttable`（ForeignKey，删除策略 `models.DO_NOTHING`）
- `parentplasmidtable.SonPlasmidID` -> `Plasmidneed`（ForeignKey，删除策略 `models.DO_NOTHING`）
- `parentplasmidtable.ParentPlasmidID` -> `Plasmidneed`（ForeignKey，删除策略 `models.DO_NOTHING`）
- `partrputable.PartID` -> `Parttable`（ForeignKey，删除策略 `models.DO_NOTHING`）
- `partscartable.part_id` -> `Parttable`（ForeignKey，删除策略 `models.CASCADE`）
- `plasmid_culture_functions.plasmid_id` -> `Plasmidneed`（ForeignKey，删除策略 `models.DO_NOTHING`）
- `plasmidscartable.PlasmidID` -> `Plasmidneed`（ForeignKey，删除策略 `models.CASCADE`）
- `plasmidunessential.PlasmidID` -> `Plasmidneed`（ForeignKey，删除策略 `models.DO_NOTHING`）
- `strain_genotype_table.plasmidid` -> `Plasmidneed`（ForeignKey，删除策略 `models.CASCADE`）
- `strain_genotype_table.strainid` -> `Straintable`（ForeignKey，删除策略 `models.CASCADE`）
- `tb_backbone_userfileaddress.userid` -> `User`（ForeignKey，删除策略 `models.DO_NOTHING`）
- `tb_backbone_userfileaddress.backboneid` -> `Backbonetable`（ForeignKey，删除策略 `models.DO_NOTHING`）
- `tb_part_userfileaddress.userid` -> `User`（ForeignKey，删除策略 `models.DO_NOTHING`）
- `tb_part_userfileaddress.partid` -> `Parttable`（ForeignKey，删除策略 `models.DO_NOTHING`）
- `tb_plasmid_userfileaddress.userid` -> `User`（ForeignKey，删除策略 `models.DO_NOTHING`）
- `tb_plasmid_userfileaddress.plasmidid` -> `Plasmidneed`（ForeignKey，删除策略 `models.DO_NOTHING`）
- `temporaryrepository.userid` -> `CustomUser`（ForeignKey，删除策略 `models.DO_NOTHING`）
- `UserProfile.user` -> `CustomUser`（OneToOneField，删除策略 `models.CASCADE`）
- `visitorprofile.created_by_user_id` -> `CustomUser`（ForeignKey，删除策略 `models.SET_NULL`）
- `visitoraccesslog.visitor_id` -> `VisitorProfile`（ForeignKey，删除策略 `models.CASCADE`）
- `visitorfeedback.visitor_id` -> `VisitorProfile`（ForeignKey，删除策略 `models.CASCADE`）
- `BackboneFeatureTable.backboneid` -> `Backbonetable`（ForeignKey，删除策略 `models.CASCADE`）
- `PartFeatureTable.partid` -> `Parttable`（ForeignKey，删除策略 `models.CASCADE`）
- `PlasmidFeatureTable.plasmidid` -> `Plasmidneed`（ForeignKey，删除策略 `models.CASCADE`）

## 历史/兼容表关系

- `backbone_culture_functions.backbone` -> `Backbonetable`（ForeignKey，删除策略 `models.DO_NOTHING`）
- `plasmid_culture_functions.plasmid` -> `Plasmidneed`（ForeignKey，删除策略 `models.DO_NOTHING`）

## 当前生效表明细

### 权限与用户

#### `auth_group`（模型 `AuthGroup`）

- `managed`：`False`

| 字段 | Django 类型 | 说明 |
| --- | --- | --- |
| `name` | `CharField` | 唯一；最大长度 150 |

#### `auth_group_permissions`（模型 `AuthGroupPermissions`）

- `managed`：`False`
- `unique_together`：`(('group', 'permission'),)`

| 字段 | Django 类型 | 说明 |
| --- | --- | --- |
| `id` | `BigAutoField` | 主键 |
| `group` | `ForeignKey` | 关联 AuthGroup；删除策略 models.DO_NOTHING |
| `permission` | `ForeignKey` | 关联 AuthPermission；删除策略 models.DO_NOTHING |

#### `auth_permission`（模型 `AuthPermission`）

- `managed`：`False`
- `unique_together`：`(('content_type', 'codename'),)`

| 字段 | Django 类型 | 说明 |
| --- | --- | --- |
| `name` | `CharField` | 最大长度 255 |
| `content_type` | `ForeignKey` | 关联 DjangoContentType；删除策略 models.DO_NOTHING |
| `codename` | `CharField` | 最大长度 100 |

#### `auth_user`（模型 `AuthUser`）

- `managed`：`False`

| 字段 | Django 类型 | 说明 |
| --- | --- | --- |
| `password` | `CharField` | 最大长度 128 |
| `last_login` | `DateTimeField` | 可为空 |
| `is_superuser` | `IntegerField` | 普通字段 |
| `username` | `CharField` | 唯一；最大长度 150 |
| `first_name` | `CharField` | 最大长度 150 |
| `last_name` | `CharField` | 最大长度 150 |
| `email` | `CharField` | 最大长度 254 |
| `is_staff` | `IntegerField` | 普通字段 |
| `is_active` | `IntegerField` | 普通字段 |
| `date_joined` | `DateTimeField` | 普通字段 |

#### `auth_user_groups`（模型 `AuthUserGroups`）

- `managed`：`False`
- `unique_together`：`(('user', 'group'),)`

| 字段 | Django 类型 | 说明 |
| --- | --- | --- |
| `id` | `BigAutoField` | 主键 |
| `user` | `ForeignKey` | 关联 AuthUser；删除策略 models.DO_NOTHING |
| `group` | `ForeignKey` | 关联 AuthGroup；删除策略 models.DO_NOTHING |

#### `auth_user_user_permissions`（模型 `AuthUserUserPermissions`）

- `managed`：`False`
- `unique_together`：`(('user', 'permission'),)`

| 字段 | Django 类型 | 说明 |
| --- | --- | --- |
| `id` | `BigAutoField` | 主键 |
| `user` | `ForeignKey` | 关联 AuthUser；删除策略 models.DO_NOTHING |
| `permission` | `ForeignKey` | 关联 AuthPermission；删除策略 models.DO_NOTHING |

#### `django_admin_log`（模型 `DjangoAdminLog`）

- `managed`：`False`

| 字段 | Django 类型 | 说明 |
| --- | --- | --- |
| `action_time` | `DateTimeField` | 普通字段 |
| `object_id` | `TextField` | 可为空 |
| `object_repr` | `CharField` | 最大长度 200 |
| `action_flag` | `PositiveSmallIntegerField` | 普通字段 |
| `change_message` | `TextField` | 普通字段 |
| `content_type` | `ForeignKey` | 关联 DjangoContentType；可为空；删除策略 models.DO_NOTHING |
| `user` | `ForeignKey` | 关联 AuthUser；删除策略 models.DO_NOTHING |

#### `django_content_type`（模型 `DjangoContentType`）

- `managed`：`False`
- `unique_together`：`(('app_label', 'model'),)`

| 字段 | Django 类型 | 说明 |
| --- | --- | --- |
| `app_label` | `CharField` | 最大长度 100 |
| `model` | `CharField` | 最大长度 100 |

#### `django_migrations`（模型 `DjangoMigrations`）

- `managed`：`False`

| 字段 | Django 类型 | 说明 |
| --- | --- | --- |
| `id` | `BigAutoField` | 主键 |
| `app` | `CharField` | 最大长度 255 |
| `name` | `CharField` | 最大长度 255 |
| `applied` | `DateTimeField` | 普通字段 |

#### `django_session`（模型 `DjangoSession`）

- `managed`：`False`

| 字段 | Django 类型 | 说明 |
| --- | --- | --- |
| `session_key` | `CharField` | 主键；最大长度 40 |
| `session_data` | `TextField` | 普通字段 |
| `expire_date` | `DateTimeField` | 普通字段 |

#### `user`（模型 `User`）

- `managed`：`True`

| 字段 | Django 类型 | 说明 |
| --- | --- | --- |
| `uid` | `AutoField` | 主键 |
| `uname` | `CharField` | 最大长度 50 |
| `email` | `CharField` | 可为空；最大长度 50 |
| `create_time` | `DateField` | 可为空 |
| `password` | `CharField` | 最大长度 50 |

#### `CustomUser`（模型 `CustomUser`）

- `managed`：`True`

| 字段 | Django 类型 | 说明 |
| --- | --- | --- |
| `uid` | `AutoField` | 主键 |
| `uname` | `CharField` | 最大长度 50 |
| `role` | `CharField` | 最大长度 20；默认值 UserRole.USER；枚举 UserRole.choices |
| `email` | `CharField` | 可为空；最大长度 50 |
| `is_email_verified` | `BooleanField` | 默认值 False |
| `last_activate` | `DateTimeField` | 普通字段 |
| `create_time` | `DateField` | 可为空 |
| `password` | `CharField` | 最大长度 500；默认值 f06a53bb5da60c512506097e48203d4c |

#### `UserProfile`（模型 `UserProfile`）

- `managed`：`True`

| 字段 | Django 类型 | 说明 |
| --- | --- | --- |
| `user` | `OneToOneField` | 关联 CustomUser；删除策略 models.CASCADE |
| `show_email` | `BooleanField` | 默认值 False |
| `show_phone` | `BooleanField` | 默认值 False |
| `create_at` | `DateTimeField` | 普通字段 |

#### `visitorprofile`（模型 `VisitorProfile`）

- `managed`：`True`

| 字段 | Django 类型 | 说明 |
| --- | --- | --- |
| `id` | `BigAutoField` | 主键 |
| `visitor_uuid` | `CharField` | 唯一；最大长度 36 |
| `institution` | `CharField` | 最大长度 255 |
| `lab_name` | `CharField` | 最大长度 255 |
| `person_name` | `CharField` | 最大长度 255 |
| `cookie_key` | `CharField` | 唯一；可为空；最大长度 128 |
| `visit_count` | `PositiveIntegerField` | 默认值 0 |
| `first_seen_at` | `DateTimeField` | 默认值 timezone.now |
| `last_seen_at` | `DateTimeField` | 默认值 timezone.now |
| `last_path` | `CharField` | 可为空；最大长度 255 |
| `last_ip` | `CharField` | 可为空；最大长度 45 |
| `last_user_agent` | `CharField` | 可为空；最大长度 512 |
| `created_by_user` | `ForeignKey` | 关联 CustomUser；可为空；对应列名 created_by_user_id；删除策略 models.SET_NULL |
| `created_at` | `DateTimeField` | 默认值 timezone.now |
| `updated_at` | `DateTimeField` | 普通字段 |

#### `visitoraccesslog`（模型 `VisitorAccessLog`）

- `managed`：`True`

| 字段 | Django 类型 | 说明 |
| --- | --- | --- |
| `id` | `BigAutoField` | 主键 |
| `visitor` | `ForeignKey` | 关联 VisitorProfile；对应列名 visitor_id；删除策略 models.CASCADE |
| `visited_at` | `DateTimeField` | 默认值 timezone.now |
| `path` | `CharField` | 最大长度 255 |
| `method` | `CharField` | 最大长度 16；默认值 GET |
| `ip` | `CharField` | 可为空；最大长度 45 |
| `user_agent` | `CharField` | 可为空；最大长度 512 |
| `referer` | `CharField` | 可为空；最大长度 512 |
| `cookie_snapshot` | `JSONField` | 可为空 |

#### `visitorfeedback`（模型 `VisitorFeedback`）

- `managed`：`True`

| 字段 | Django 类型 | 说明 |
| --- | --- | --- |
| `visitor_profile` | `ForeignKey` | 关联 VisitorProfile；对应列名 visitor_id |
| `feedback_type` | `CharField` | 最大长度 32；枚举 FEEDBACK_TYPE_CHOICES |
| `title` | `CharField` | 最大长度 200 |
| `content` | `TextField` | 普通字段 |
| `contact_email` | `EmailField` | 可留空 |
| `page_path` | `CharField` | 可留空；最大长度 255 |
| `status` | `CharField` | 最大长度 32；默认值 STATUS_PENDING；枚举 STATUS_CHOICES |
| `created_at` | `DateTimeField` | 普通字段 |
| `updated_at` | `DateTimeField` | 普通字段 |

### 骨架 Backbone

#### `backbone_culture_functions`（模型 `Backbone_Culture_Functions`）

- `managed`：`True`

| 字段 | Django 类型 | 说明 |
| --- | --- | --- |
| `bcfid` | `AutoField` | 主键 |
| `backbone_id` | `ForeignKey` | 关联 Backbonetable；对应列名 backbone_id；删除策略 models.CASCADE |
| `function_content` | `CharField` | 最大长度 50 |
| `function_type` | `CharField` | 最大长度 50 |

#### `backbonescartable`（模型 `Backbonescartable`）

- `managed`：`True`

| 字段 | Django 类型 | 说明 |
| --- | --- | --- |
| `backbonescarid` | `AutoField` | 主键；对应列名 BackboneScarID |
| `backboneid` | `ForeignKey` | 关联 Backbonetable；对应列名 BackboneID；删除策略 models.CASCADE |
| `bsmbi` | `CharField` | 最大长度 100；对应列名 BsmBI |
| `bsai` | `CharField` | 最大长度 100；对应列名 BsaI |
| `bbsi` | `CharField` | 最大长度 100；对应列名 BbsI |
| `aari` | `CharField` | 最大长度 100；对应列名 AarI |
| `sapi` | `CharField` | 最大长度 100；对应列名 SapI |

#### `backbonetable`（模型 `Backbonetable`）

- `managed`：`True`

| 字段 | Django 类型 | 说明 |
| --- | --- | --- |
| `id` | `AutoField` | 主键；对应列名 ID |
| `name` | `CharField` | 最大长度 20；对应列名 Name |
| `length` | `IntegerField` | 可为空；对应列名 Length |
| `sequence` | `TextField` | 对应列名 Sequence |
| `species` | `CharField` | 可为空；最大长度 50；对应列名 Species |
| `copynumber` | `CharField` | 可为空；最大长度 20；对应列名 CopyNumber |
| `notes` | `TextField` | 可为空；对应列名 Notes |
| `alias` | `CharField` | 可为空；最大长度 500；对应列名 Alias |
| `user` | `CharField` | 最大长度 50；对应列名 User |
| `tag` | `CharField` | 可为空；最大长度 50 |
| `updatedate` | `DateTimeField` | 可为空 |
| `uploaddate` | `DateTimeField` | 可为空 |

#### `parentbackbonetable`（模型 `Parentbackbonetable`）

- `managed`：`True`

| 字段 | Django 类型 | 说明 |
| --- | --- | --- |
| `pbid` | `AutoField` | 主键 |
| `sonplasmidid` | `ForeignKey` | 关联 Plasmidneed；对应列名 sonplasmidid；删除策略 models.DO_NOTHING |
| `parentbackboneid` | `ForeignKey` | 关联 Backbonetable；对应列名 parentbackboneid；删除策略 models.DO_NOTHING |

#### `tb_backbone_userfileaddress`（模型 `TbBackboneUserfileaddress`）

- `managed`：`True`

| 字段 | Django 类型 | 说明 |
| --- | --- | --- |
| `ufid` | `AutoField` | 主键 |
| `userid` | `ForeignKey` | 关联 User；可为空；对应列名 userid；删除策略 models.DO_NOTHING |
| `backboneid` | `ForeignKey` | 关联 Backbonetable；可为空；对应列名 backboneid；删除策略 models.DO_NOTHING |
| `fileaddress` | `TextField` | 可为空 |

#### `BackboneFeatureTable`（模型 `Backbonefeaturetable`）

- `managed`：`True`

| 字段 | Django 类型 | 说明 |
| --- | --- | --- |
| `bfif` | `AutoField` | 主键 |
| `backboneid` | `ForeignKey` | 关联 Backbonetable；对应列名 backboneid；删除策略 models.CASCADE |
| `feature_start` | `IntegerField` | 普通字段 |
| `feature_end` | `IntegerField` | 普通字段 |
| `feature_type` | `CharField` | 最大长度 50 |
| `feature_label` | `CharField` | 最大长度 50 |
| `feature_color` | `CharField` | 最大长度 50 |
| `feature_apeinfo` | `CharField` | 最大长度 50 |

### 实验与辅助数据

#### `dbdtable`（模型 `Dbdtable`）

- `managed`：`True`

| 字段 | Django 类型 | 说明 |
| --- | --- | --- |
| `id` | `AutoField` | 主键；对应列名 ID |
| `name` | `CharField` | 最大长度 20；对应列名 Name |
| `i0` | `FloatField` | 对应列名 I0 |
| `kd` | `FloatField` | 普通字段 |

#### `gates`（模型 `Gates`）

- `managed`：`False`

| 字段 | Django 类型 | 说明 |
| --- | --- | --- |
| `collection` | `CharField` | 可为空；最大长度 100 |
| `name` | `CharField` | 可为空；最大长度 100 |
| `system` | `CharField` | 可为空；最大长度 100 |
| `group` | `CharField` | 可为空；最大长度 100 |
| `regulator` | `CharField` | 可为空；最大长度 100 |
| `gate_type` | `CharField` | 可为空；最大长度 100 |
| `color` | `CharField` | 可为空；最大长度 100 |
| `model` | `CharField` | 可为空；最大长度 100 |
| `structure` | `CharField` | 可为空；最大长度 100 |

#### `gatetabletest`（模型 `Gatetabletest`）

- `managed`：`False`

| 字段 | Django 类型 | 说明 |
| --- | --- | --- |
| `gateid` | `IntegerField` | 可为空；对应列名 GateID |
| `gatename` | `CharField` | 可为空；最大长度 100；对应列名 GateName |
| `gatetype` | `CharField` | 可为空；最大长度 100；对应列名 GateType |
| `responsefunction` | `CharField` | 可为空；最大长度 100；对应列名 ResponseFunction |
| `parameter1` | `FloatField` | 可为空；对应列名 Parameter1 |
| `parameter2` | `FloatField` | 可为空；对应列名 Parameter2 |
| `parameter3` | `FloatField` | 可为空；对应列名 Parameter3 |
| `parameter4` | `FloatField` | 可为空；对应列名 Parameter4 |
| `xmin` | `FloatField` | 可为空；对应列名 Xmin |
| `xmax` | `FloatField` | 可为空；对应列名 Xmax |
| `gatepromoterid` | `IntegerField` | 可为空；对应列名 GatePromoterID |
| `gaterbsid` | `IntegerField` | 可为空；对应列名 GateRBSID |
| `gatecdsid` | `IntegerField` | 可为空；对应列名 GateCDSID |
| `gateterminatorid` | `IntegerField` | 可为空；对应列名 GateTerminatorID |

#### `gbptest`（模型 `Gbptest`）

- `managed`：`False`

| 字段 | Django 类型 | 说明 |
| --- | --- | --- |
| `index` | `BigIntegerField` | 可为空 |
| `partid` | `BigIntegerField` | 可为空；对应列名 PartID |
| `alias` | `TextField` | 可为空 |
| `up` | `TextField` | 可为空；对应列名 UP |
| `co_35` | `TextField` | 可为空 |
| `spacer` | `TextField` | 可为空 |
| `ext_10` | `TextField` | 可为空 |
| `co_10` | `TextField` | 可为空 |
| `disc` | `TextField` | 可为空 |
| `utr` | `TextField` | 可为空；对应列名 UTR |
| `note` | `TextField` | 可为空；对应列名 Note |
| `rpu11` | `FloatField` | 可为空；对应列名 RPU11 |
| `rpu12` | `FloatField` | 可为空；对应列名 RPU12 |
| `rpu13` | `FloatField` | 可为空；对应列名 RPU13 |
| `aveg1` | `FloatField` | 可为空；对应列名 Aveg1 |
| `rawdatafile1` | `TextField` | 可为空；对应列名 RawDataFile1 |
| `rpu21` | `FloatField` | 可为空；对应列名 RPU21 |
| `rpu22` | `FloatField` | 可为空；对应列名 RPU22 |
| `rpu23` | `FloatField` | 可为空；对应列名 RPU23 |
| `aveg2` | `FloatField` | 可为空；对应列名 Aveg2 |
| `rawdatafile2` | `TextField` | 可为空；对应列名 RawDataFile2 |
| `unnamed_20` | `FloatField` | 可为空；对应列名 Unnamed: 20 |
| `unnamed_21` | `FloatField` | 可为空；对应列名 Unnamed: 21 |
| `unnamed_22` | `FloatField` | 可为空；对应列名 Unnamed: 22 |
| `unnamed_23` | `FloatField` | 可为空；对应列名 Unnamed: 23 |
| `unnamed_24` | `FloatField` | 可为空；对应列名 Unnamed: 24 |

#### `gubangpromoterlibrary`（模型 `Gubangpromoterlibrary`）

- `managed`：`False`

| 字段 | Django 类型 | 说明 |
| --- | --- | --- |
| `partid` | `IntegerField` | 可为空；对应列名 PartID |
| `alias` | `CharField` | 可为空；最大长度 100 |
| `up` | `CharField` | 可为空；最大长度 100；对应列名 UP |
| `co_35` | `CharField` | 可为空；最大长度 100；对应列名 co_-35 |
| `spacer` | `CharField` | 可为空；最大长度 100 |
| `ext_10` | `CharField` | 可为空；最大长度 100；对应列名 ext-10 |
| `co_10` | `CharField` | 可为空；最大长度 100；对应列名 co_-10 |
| `disc` | `CharField` | 可为空；最大长度 100 |
| `utr` | `CharField` | 可为空；最大长度 100；对应列名 UTR |
| `note` | `CharField` | 可为空；最大长度 100；对应列名 Note |
| `tset1_rpu1` | `FloatField` | 可为空；对应列名 tset1_RPU1 |
| `test1_rpu2` | `FloatField` | 可为空；对应列名 test1_RPU2 |
| `test1_rpu3` | `FloatField` | 可为空；对应列名 test1_RPU3 |
| `test1_aveg` | `FloatField` | 可为空；对应列名 test1_Aveg |
| `test1_rawdatafile` | `CharField` | 可为空；最大长度 100；对应列名 test1_RawDataFile |
| `test2_rpu1` | `FloatField` | 可为空；对应列名 test2_RPU1 |
| `test2_rpu2` | `FloatField` | 可为空；对应列名 test2_RPU2 |
| `test2_rpu3` | `FloatField` | 可为空；对应列名 test2_RPU3 |
| `test2_aveg` | `FloatField` | 可为空；对应列名 test2_Aveg |
| `test2_rawdatafile` | `CharField` | 可为空；最大长度 100；对应列名 test2_RawDataFile |

#### `lbddimertable`（模型 `Lbddimertable`）

- `managed`：`True`

| 字段 | Django 类型 | 说明 |
| --- | --- | --- |
| `id` | `AutoField` | 主键；对应列名 ID |
| `name` | `CharField` | 最大长度 20；对应列名 Name |
| `k1` | `FloatField` | 普通字段 |
| `k2` | `FloatField` | 普通字段 |
| `k3` | `FloatField` | 普通字段 |
| `i` | `FloatField` | 对应列名 I |

#### `lbdnrtable`（模型 `Lbdnrtable`）

- `managed`：`True`

| 字段 | Django 类型 | 说明 |
| --- | --- | --- |
| `id` | `AutoField` | 主键；对应列名 ID |
| `name` | `CharField` | 最大长度 20；对应列名 Name |
| `k1` | `FloatField` | 普通字段 |
| `k2` | `FloatField` | 普通字段 |
| `k3` | `FloatField` | 普通字段 |
| `kx1` | `FloatField` | 普通字段 |
| `kx2` | `FloatField` | 普通字段 |

#### `structures`（模型 `Structures`）

- `managed`：`False`

| 字段 | Django 类型 | 说明 |
| --- | --- | --- |
| `collection` | `CharField` | 可为空；最大长度 100 |
| `name` | `CharField` | 可为空；最大长度 100 |
| `inputs` | `CharField` | 可为空；最大长度 100 |
| `outputs` | `CharField` | 可为空；最大长度 100 |
| `devices` | `CharField` | 可为空；最大长度 500 |

#### `temporaryrepository`（模型 `Temporaryrepository`）

- `managed`：`True`

| 字段 | Django 类型 | 说明 |
| --- | --- | --- |
| `id` | `CharField` | 主键；最大长度 32 |
| `userid` | `ForeignKey` | 关联 CustomUser；对应列名 userid；删除策略 models.DO_NOTHING |
| `repositorycreate_time` | `DateTimeField` | 可为空 |
| `repositoryupdate_time` | `DateTimeField` | 可为空 |
| `repositoryexpire_time` | `DateTimeField` | 可为空 |
| `data` | `JSONField` | 可为空 |
| `name` | `CharField` | 可为空；最大长度 500 |
| `note` | `TextField` | 可为空；对应列名 Note |
| `alias` | `CharField` | 可为空；最大长度 100；对应列名 alias |
| `level` | `IntegerField` | 可为空；对应列名 Level |
| `part_start_scar` | `CharField` | 可为空；最大长度 10；对应列名 part_start_scar |
| `part_end_scar` | `CharField` | 可为空；最大长度 10；对应列名 part_end_scar |

#### `testdatatable`（模型 `Testdatatable`）

- `managed`：`False`

| 字段 | Django 类型 | 说明 |
| --- | --- | --- |
| `testdataid` | `AutoField` | 主键；对应列名 TestDataID |
| `testdataname` | `CharField` | 最大长度 20；对应列名 TestDataName |
| `purpose` | `TextField` | 可为空；对应列名 Purpose |
| `standardstrain` | `CharField` | 可为空；最大长度 30；对应列名 StandardStrain |
| `positivecontrol` | `CharField` | 可为空；最大长度 100；对应列名 PositiveControl |
| `dataaddress` | `TextField` | 可为空；对应列名 DataAddress |
| `date` | `TextField` | 可为空；对应列名 Date |
| `strain` | `CharField` | 最大长度 100；对应列名 Strain |

#### `yeastmodels`（模型 `Yeastmodels`）

- `managed`：`False`

| 字段 | Django 类型 | 说明 |
| --- | --- | --- |
| `collection` | `CharField` | 可为空；最大长度 100 |
| `name` | `CharField` | 可为空；最大长度 100 |
| `function1` | `CharField` | 可为空；最大长度 100 |
| `function2` | `CharField` | 可为空；最大长度 100 |
| `toxicity` | `CharField` | 可为空；最大长度 100 |
| `cytometry` | `CharField` | 可为空；最大长度 100 |
| `ymax` | `FloatField` | 可为空 |
| `ymin` | `FloatField` | 可为空 |
| `k_value` | `FloatField` | 可为空 |
| `n_value` | `FloatField` | 可为空 |

### 元件 Part

#### `parentparttable`（模型 `Parentparttable`）

- `managed`：`True`

| 字段 | Django 类型 | 说明 |
| --- | --- | --- |
| `ppid` | `AutoField` | 主键 |
| `sonplasmidid` | `ForeignKey` | 关联 Plasmidneed；对应列名 sonplasmidid；删除策略 models.DO_NOTHING |
| `parentpartid` | `ForeignKey` | 关联 Parttable；对应列名 parentpartid；删除策略 models.DO_NOTHING |

#### `partrputable`（模型 `Partrputable`）

- `managed`：`True`

| 字段 | Django 类型 | 说明 |
| --- | --- | --- |
| `prid` | `AutoField` | 主键；对应列名 PRID |
| `partid` | `ForeignKey` | 关联 Parttable；对应列名 PartID；删除策略 models.DO_NOTHING |
| `rpu` | `FloatField` | 对应列名 RPU |
| `teststrain` | `CharField` | 可为空；最大长度 50；对应列名 TestStrain |
| `note` | `CharField` | 可为空；最大长度 100；对应列名 Note |

#### `parts`（模型 `Parts`）

- `managed`：`False`

| 字段 | Django 类型 | 说明 |
| --- | --- | --- |
| `collection` | `CharField` | 可为空；最大长度 100 |
| `type` | `CharField` | 可为空；最大长度 100 |
| `name` | `CharField` | 可为空；最大长度 100 |
| `dnasequence` | `CharField` | 可为空；最大长度 100 |
| `parameters` | `CharField` | 可为空；最大长度 100 |

#### `partscartable`（模型 `Partscartable`）

- `managed`：`True`

| 字段 | Django 类型 | 说明 |
| --- | --- | --- |
| `partscarid` | `AutoField` | 主键；对应列名 PartScarID |
| `part_id` | `ForeignKey` | 关联 Parttable；对应列名 part_id；删除策略 models.CASCADE |
| `bsmbi` | `CharField` | 最大长度 100；对应列名 BsmBI |
| `bsai` | `CharField` | 最大长度 100；对应列名 BsaI |
| `bbsi` | `CharField` | 最大长度 100；对应列名 BbsI |
| `aari` | `CharField` | 最大长度 100；对应列名 AarI |
| `sapi` | `CharField` | 最大长度 100；对应列名 SapI |

#### `parttable`（模型 `Parttable`）

- `managed`：`True`

| 字段 | Django 类型 | 说明 |
| --- | --- | --- |
| `partid` | `AutoField` | 主键；对应列名 PartID |
| `name` | `CharField` | 可为空；最大长度 100；对应列名 Name |
| `alias` | `CharField` | 可为空；最大长度 100；对应列名 Alias |
| `lengthinlevel0` | `IntegerField` | 对应列名 LengthInLevel0 |
| `level0sequence` | `TextField` | 可为空；对应列名 Level0Sequence |
| `confirmedsequence` | `TextField` | 可为空；对应列名 ConfirmedSequence |
| `insertsequence` | `TextField` | 可为空；对应列名 InsertSequence |
| `sourceorganism` | `TextField` | 可为空；对应列名 SourceOrganism |
| `reference` | `TextField` | 可为空；对应列名 Reference |
| `note` | `TextField` | 可为空；对应列名 Note |
| `type` | `IntegerField` | 对应列名 Type |
| `user` | `CharField` | 可为空；最大长度 50；对应列名 User |
| `tag` | `CharField` | 可为空；最大长度 50 |
| `uploaddate` | `DateTimeField` | 可为空 |
| `updatedate` | `DateTimeField` | 可为空 |

#### `tb_part_userfileaddress`（模型 `TbPartUserfileaddress`）

- `managed`：`True`

| 字段 | Django 类型 | 说明 |
| --- | --- | --- |
| `ufid` | `AutoField` | 主键 |
| `userid` | `ForeignKey` | 关联 User；可为空；对应列名 userid；删除策略 models.DO_NOTHING |
| `partid` | `ForeignKey` | 关联 Parttable；可为空；对应列名 partid；删除策略 models.DO_NOTHING |
| `fileaddress` | `TextField` | 可为空 |

#### `yeastparts`（模型 `Yeastparts`）

- `managed`：`False`

| 字段 | Django 类型 | 说明 |
| --- | --- | --- |
| `name` | `CharField` | 可为空；最大长度 100 |
| `type` | `CharField` | 可为空；最大长度 100 |
| `dnasequence` | `CharField` | 可为空；最大长度 100 |
| `strength` | `FloatField` | 可为空 |

#### `PartFeatureTable`（模型 `Partfeaturetable`）

- `managed`：`True`

| 字段 | Django 类型 | 说明 |
| --- | --- | --- |
| `pfid` | `AutoField` | 主键 |
| `partid` | `ForeignKey` | 关联 Parttable；对应列名 partid；删除策略 models.CASCADE |
| `feature_start` | `IntegerField` | 普通字段 |
| `feature_end` | `IntegerField` | 普通字段 |
| `feature_type` | `CharField` | 最大长度 50 |
| `feature_label` | `CharField` | 最大长度 50 |
| `feature_color` | `CharField` | 最大长度 50 |
| `feature_apeinfo` | `CharField` | 最大长度 50 |

### 质粒 Plasmid

#### `parentplasmidtable`（模型 `Parentplasmidtable`）

- `managed`：`True`

| 字段 | Django 类型 | 说明 |
| --- | --- | --- |
| `ppid` | `AutoField` | 主键；对应列名 PPID |
| `sonplasmidid` | `ForeignKey` | 关联 Plasmidneed；对应列名 SonPlasmidID；删除策略 models.DO_NOTHING |
| `parentplasmidid` | `ForeignKey` | 关联 Plasmidneed；对应列名 ParentPlasmidID；删除策略 models.DO_NOTHING |

#### `plasmid_culture_functions`（模型 `Plasmid_Culture_Functions`）

- `managed`：`True`

| 字段 | Django 类型 | 说明 |
| --- | --- | --- |
| `pcfid` | `AutoField` | 主键 |
| `plasmid_id` | `ForeignKey` | 关联 Plasmidneed；对应列名 plasmid_id；删除策略 models.DO_NOTHING |
| `function_content` | `CharField` | 最大长度 100 |
| `function_type` | `CharField` | 最大长度 100 |

#### `plasmidneed`（模型 `Plasmidneed`）

- `managed`：`True`

| 字段 | Django 类型 | 说明 |
| --- | --- | --- |
| `plasmidid` | `AutoField` | 主键；对应列名 PlasmidID |
| `name` | `CharField` | 可为空；最大长度 20；对应列名 Name |
| `level` | `CharField` | 最大长度 10；对应列名 Level |
| `length` | `IntegerField` | 对应列名 Length |
| `sequenceconfirm` | `TextField` | 对应列名 SequenceConfirm |
| `plate` | `CharField` | 可为空；最大长度 100；对应列名 Plate |
| `state` | `IntegerField` | 可为空；对应列名 State |
| `user` | `CharField` | 最大长度 20；对应列名 User |
| `note` | `CharField` | 可为空；最大长度 500；对应列名 Note |
| `alias` | `CharField` | 可为空；最大长度 500；对应列名 Alias |
| `customparentinformation` | `TextField` | 可为空；对应列名 CustomParentInformation |
| `tag` | `CharField` | 可为空；最大长度 50 |
| `uploaddate` | `DateTimeField` | 可为空 |
| `updatedate` | `DateTimeField` | 可为空 |

#### `plasmidscartable`（模型 `Plasmidscartable`）

- `managed`：`True`

| 字段 | Django 类型 | 说明 |
| --- | --- | --- |
| `plasmidscarid` | `AutoField` | 主键；对应列名 PlasmidScarID |
| `plasmidid` | `ForeignKey` | 关联 Plasmidneed；对应列名 PlasmidID；删除策略 models.CASCADE |
| `bsmbi` | `CharField` | 最大长度 100；对应列名 BsmBI |
| `bsai` | `CharField` | 最大长度 100；对应列名 BsaI |
| `bbsi` | `CharField` | 最大长度 100；对应列名 BbsI |
| `aari` | `CharField` | 最大长度 100；对应列名 AarI |
| `sapi` | `CharField` | 最大长度 100；对应列名 SapI |

#### `plasmidunessential`（模型 `Plasmidunessential`）

- `managed`：`False`

| 字段 | Django 类型 | 说明 |
| --- | --- | --- |
| `id` | `AutoField` | 主键；对应列名 ID |
| `plasmidid` | `ForeignKey` | 关联 Plasmidneed；对应列名 PlasmidID；删除策略 models.DO_NOTHING |
| `alias` | `CharField` | 可为空；最大长度 20；对应列名 Alias |
| `avaliable` | `IntegerField` | 可为空；对应列名 Avaliable |
| `function` | `TextField` | 可为空；对应列名 Function |
| `reference` | `TextField` | 可为空；对应列名 Reference |
| `sourceorganism` | `TextField` | 可为空；对应列名 SourceOrganism |
| `comment` | `TextField` | 可为空；对应列名 Comment |
| `seqfileaddress` | `TextField` | 可为空；对应列名 SeqFileAddress |

#### `tb_plasmid_userfileaddress`（模型 `TbPlasmidUserfileaddress`）

- `managed`：`True`

| 字段 | Django 类型 | 说明 |
| --- | --- | --- |
| `ufid` | `AutoField` | 主键 |
| `userid` | `ForeignKey` | 关联 User；可为空；对应列名 userid；删除策略 models.DO_NOTHING |
| `plasmidid` | `ForeignKey` | 关联 Plasmidneed；可为空；对应列名 plasmidid；删除策略 models.DO_NOTHING |
| `fileaddress` | `TextField` | 可为空 |

#### `PlasmidFeatureTable`（模型 `Plasmidfeaturetable`）

- `managed`：`True`

| 字段 | Django 类型 | 说明 |
| --- | --- | --- |
| `pfid` | `AutoField` | 主键 |
| `plasmidid` | `ForeignKey` | 关联 Plasmidneed；对应列名 plasmidid；删除策略 models.CASCADE |
| `feature_start` | `IntegerField` | 普通字段 |
| `feature_end` | `IntegerField` | 普通字段 |
| `feature_type` | `CharField` | 最大长度 50 |
| `feature_label` | `CharField` | 最大长度 50 |
| `feature_color` | `CharField` | 最大长度 50 |
| `feature_apeinfo` | `CharField` | 最大长度 50 |

### 菌株 Strain

#### `straintable`（模型 `Straintable`）

- `managed`：`True`

| 字段 | Django 类型 | 说明 |
| --- | --- | --- |
| `strainid` | `AutoField` | 主键；对应列名 StrainID |
| `strainname` | `CharField` | 最大长度 20；对应列名 StrainName |
| `background` | `CharField` | 最大长度 20；对应列名 Background |
| `marker` | `CharField` | 最大长度 30；对应列名 Marker |
| `store` | `CharField` | 最大长度 100；对应列名 Store |

#### `strain_genotype_table`（模型 `StrainGenotypeTable`）

- `managed`：`True`

| 字段 | Django 类型 | 说明 |
| --- | --- | --- |
| `sgid` | `AutoField` | 主键；对应列名 sdid |
| `plasmidid` | `ForeignKey` | 关联 Plasmidneed；对应列名 plasmidid；删除策略 models.CASCADE |
| `strainid` | `ForeignKey` | 关联 Straintable；对应列名 strainid；删除策略 models.CASCADE |

## 历史/兼容表明细

### 骨架 Backbone

#### `backbone_culture_functions`（模型 `BackboneCultureFunctions`）

- `managed`：`False`

| 字段 | Django 类型 | 说明 |
| --- | --- | --- |
| `bcfid` | `AutoField` | 主键 |
| `backbone` | `ForeignKey` | 关联 Backbonetable；删除策略 models.DO_NOTHING |
| `function_content` | `CharField` | 最大长度 50 |
| `function_type` | `CharField` | 最大长度 50 |

### 实验与辅助数据

#### `gbp`（模型 `Gbp`）

- `managed`：`False`

| 字段 | Django 类型 | 说明 |
| --- | --- | --- |
| `index` | `BigIntegerField` | 可为空 |
| `id` | `FloatField` | 可为空；对应列名 ID |
| `plasmidid` | `FloatField` | 可为空；对应列名 PlasmidID |
| `alias` | `TextField` | 可为空 |
| `up` | `TextField` | 可为空；对应列名 UP |
| `co_35` | `TextField` | 可为空 |
| `spacer` | `TextField` | 可为空 |
| `ext_10` | `TextField` | 可为空 |
| `co_10` | `TextField` | 可为空 |
| `disc` | `TextField` | 可为空 |
| `utr` | `TextField` | 可为空；对应列名 UTR |
| `note` | `TextField` | 可为空；对应列名 Note |
| `rpu11` | `FloatField` | 可为空；对应列名 RPU11 |
| `rpu12` | `FloatField` | 可为空；对应列名 RPU12 |
| `rpu13` | `FloatField` | 可为空；对应列名 RPU13 |
| `aveg1` | `FloatField` | 可为空；对应列名 Aveg1 |
| `rawfiledata1` | `TextField` | 可为空；对应列名 RawFileData1 |
| `rpu21` | `FloatField` | 可为空；对应列名 RPU21 |
| `rpu22` | `FloatField` | 可为空；对应列名 RPU22 |
| `rpu23` | `FloatField` | 可为空；对应列名 RPU23 |
| `aveg2` | `FloatField` | 可为空；对应列名 Aveg2 |
| `rawfiledata2` | `TextField` | 可为空；对应列名 RawFileData2 |

#### `gubangsystemtesting`（模型 `Gubangsystemtesting`）

- `managed`：`False`

| 字段 | Django 类型 | 说明 |
| --- | --- | --- |
| `id` | `IntegerField` | 可为空；对应列名 ID |
| `plasmidid` | `IntegerField` | 可为空；对应列名 PlasmidID |
| `testnumber` | `CharField` | 可为空；最大长度 100；对应列名 TestNumber |
| `transcriptiontype` | `CharField` | 可为空；最大长度 100；对应列名 TranscriptionType |
| `promotername` | `CharField` | 可为空；最大长度 100；对应列名 PromoterName |
| `inputrpu` | `FloatField` | 可为空；对应列名 inputRPU |
| `tf_expressionlevel` | `CharField` | 可为空；最大长度 100；对应列名 TF_ExpressionLevel |
| `iptg_concentration` | `CharField` | 可为空；最大长度 100；对应列名 IPTG_Concentration |
| `uninducedintensity1` | `FloatField` | 可为空；对应列名 UninducedIntensity1 |
| `uninducedintensity2` | `FloatField` | 可为空；对应列名 UninducedIntensity2 |
| `uninducedintensity3` | `FloatField` | 可为空；对应列名 UninducedIntensity3 |
| `uninducedintensity_aveg` | `FloatField` | 可为空；对应列名 UninducedIntensity_Aveg |
| `inducedintensity1` | `FloatField` | 可为空；对应列名 InducedIntensity1 |
| `inducedintensity2` | `FloatField` | 可为空；对应列名 InducedIntensity2 |
| `inducedintensity3` | `FloatField` | 可为空；对应列名 InducedIntensity3 |
| `inducedintensity_aveg` | `FloatField` | 可为空；对应列名 InducedIntensity_Aveg |
| `inducingmultiple1` | `FloatField` | 可为空；对应列名 InducingMultiple1 |
| `inducingmultiple2` | `FloatField` | 可为空；对应列名 InducingMultiple2 |
| `inducingmultiple3` | `FloatField` | 可为空；对应列名 InducingMultiple3 |
| `inducingmultiple_aveg` | `FloatField` | 可为空；对应列名 InducingMultiple_Aveg |
| `rawdatafile` | `CharField` | 可为空；最大长度 100；对应列名 RawDataFile |

#### `kucaopromoterlibrary`（模型 `Kucaopromoterlibrary`）

- `managed`：`False`

| 字段 | Django 类型 | 说明 |
| --- | --- | --- |
| `prenote` | `CharField` | 可为空；最大长度 10；对应列名 preNote |
| `id` | `IntegerField` | 可为空；对应列名 ID |
| `partid` | `IntegerField` | 可为空；对应列名 PartID |
| `up` | `CharField` | 可为空；最大长度 100；对应列名 UP |
| `co_35` | `CharField` | 可为空；最大长度 100；对应列名 co_-35 |
| `spacer` | `CharField` | 可为空；最大长度 100 |
| `ext_10` | `CharField` | 可为空；最大长度 100；对应列名 ext-10 |
| `co_10` | `CharField` | 可为空；最大长度 100；对应列名 co_-10 |
| `disc` | `CharField` | 可为空；最大长度 100 |
| `utr` | `CharField` | 可为空；最大长度 100；对应列名 UTR |
| `note` | `CharField` | 可为空；最大长度 100；对应列名 Note |
| `test1_rpu1` | `FloatField` | 可为空；对应列名 test1_RPU1 |
| `test1_rpu2` | `FloatField` | 可为空；对应列名 test1_RPU2 |
| `test1_rpu3` | `FloatField` | 可为空；对应列名 test1_RPU3 |
| `test1_aveg` | `FloatField` | 可为空；对应列名 test1_Aveg |
| `test1_datarawfile` | `CharField` | 可为空；最大长度 100；对应列名 test1_DataRawFile |
| `test2_rpu1` | `FloatField` | 可为空；对应列名 test2_RPU1 |
| `test2_rpu2` | `FloatField` | 可为空；对应列名 test2_RPU2 |
| `test2_rpu3` | `FloatField` | 可为空；对应列名 test2_RPU3 |
| `test2_aveg` | `FloatField` | 可为空；对应列名 test2_Aveg |
| `test2_datarawfile` | `CharField` | 可为空；最大长度 100；对应列名 test2_DataRawFile |
| `test3_rpu1` | `FloatField` | 可为空；对应列名 test3_RPU1 |
| `test3_rpu2` | `FloatField` | 可为空；对应列名 test3_RPU2 |
| `test3_rpu3` | `FloatField` | 可为空；对应列名 test3_RPU3 |
| `test3_aveg` | `FloatField` | 可为空；对应列名 test3_Aveg |
| `test3_datarawfile` | `CharField` | 可为空；最大长度 100；对应列名 test3_DataRawFile |

#### `kucaosystemtesting`（模型 `Kucaosystemtesting`）

- `managed`：`False`

| 字段 | Django 类型 | 说明 |
| --- | --- | --- |
| `id` | `IntegerField` | 可为空；对应列名 ID |
| `plasmidid` | `IntegerField` | 可为空；对应列名 PlasmidID |
| `testnumber` | `CharField` | 可为空；最大长度 100；对应列名 TestNumber |
| `transcriptiontype` | `CharField` | 可为空；最大长度 100；对应列名 TranscriptionType |
| `promotername` | `CharField` | 可为空；最大长度 100；对应列名 PromoterName |
| `tf_expressionlevel` | `CharField` | 可为空；最大长度 100；对应列名 TF_ExpressionLevel |
| `inputrpu` | `FloatField` | 可为空；对应列名 inputRPU |
| `iptg_concentration` | `CharField` | 可为空；最大长度 100；对应列名 IPTG_Concentration |
| `uninducedintensity1` | `FloatField` | 可为空；对应列名 UninducedIntensity1 |
| `uninducedintensity2` | `FloatField` | 可为空；对应列名 UninducedIntensity2 |
| `uninducedintensity3` | `FloatField` | 可为空；对应列名 UninducedIntensity3 |
| `uninducedintensity_aveg` | `FloatField` | 可为空；对应列名 UninducedIntensity_Aveg |
| `inducedintensity1` | `FloatField` | 可为空；对应列名 InducedIntensity1 |
| `inducedintensity2` | `FloatField` | 可为空；对应列名 InducedIntensity2 |
| `inducedintensity3` | `FloatField` | 可为空；对应列名 InducedIntensity3 |
| `inducedintensity_aveg` | `FloatField` | 可为空；对应列名 InducedIntensity_Aveg |
| `inducingmultiple1` | `FloatField` | 可为空；对应列名 InducingMultiple1 |
| `inducingmultiple2` | `FloatField` | 可为空；对应列名 InducingMultiple2 |
| `inducingmultiple3` | `FloatField` | 可为空；对应列名 InducingMultiple3 |
| `inducingmultiple_aveg` | `FloatField` | 可为空；对应列名 InducingMultiple_Aveg |
| `rawdatafile` | `CharField` | 可为空；最大长度 100；对应列名 RawDataFile |

#### `largeintestinesystem`（模型 `Largeintestinesystem`）

- `managed`：`False`

| 字段 | Django 类型 | 说明 |
| --- | --- | --- |
| `id` | `IntegerField` | 可为空；对应列名 ID |
| `plasmidid` | `IntegerField` | 可为空；对应列名 PlasmidID |
| `testnumber` | `CharField` | 可为空；最大长度 100；对应列名 TestNumber |
| `transcriptiontype` | `CharField` | 可为空；最大长度 100；对应列名 TranscriptionType |
| `promotername` | `CharField` | 可为空；最大长度 100；对应列名 PromoterName |
| `tf_expressionlevel` | `CharField` | 可为空；最大长度 100；对应列名 TF_ExpressionLevel |
| `input_rpu` | `FloatField` | 可为空；对应列名 input_RPU |
| `iptg_concentration` | `CharField` | 可为空；最大长度 100；对应列名 IPTG_concentration |
| `uninducedintensity1` | `FloatField` | 可为空；对应列名 UninducedIntensity1 |
| `uninducedintensity2` | `FloatField` | 可为空；对应列名 UninducedIntensity2 |
| `uninducedintensity3` | `FloatField` | 可为空；对应列名 UninducedIntensity3 |
| `uninducedintensity_average` | `FloatField` | 可为空；对应列名 UninducedIntensity_Average |
| `inducedintensity1` | `FloatField` | 可为空；对应列名 InducedIntensity1 |
| `inducedintensity2` | `FloatField` | 可为空；对应列名 InducedIntensity2 |
| `inducedintensity3` | `FloatField` | 可为空；对应列名 InducedIntensity3 |
| `inducedintensity_average` | `FloatField` | 可为空；对应列名 InducedIntensity_Average |
| `inducingmultiple1` | `FloatField` | 可为空；对应列名 InducingMultiple1 |
| `inducingmultiple2` | `FloatField` | 可为空；对应列名 InducingMultiple2 |
| `inducingmultiple3` | `FloatField` | 可为空；对应列名 InducingMultiple3 |
| `inducingmultiple_average` | `FloatField` | 可为空；对应列名 InducingMultiple_Average |
| `rawdatafile` | `CharField` | 可为空；最大长度 100；对应列名 RawDataFile |

### 质粒 Plasmid

#### `plasmid_culture_functions`（模型 `PlasmidCultureFunctions`）

- `managed`：`False`

| 字段 | Django 类型 | 说明 |
| --- | --- | --- |
| `pcfid` | `AutoField` | 主键 |
| `plasmid` | `ForeignKey` | 关联 Plasmidneed；删除策略 models.DO_NOTHING |
| `function_content` | `CharField` | 最大长度 100 |
| `function_type` | `CharField` | 最大长度 100 |
