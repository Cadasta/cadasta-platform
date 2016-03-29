BEGIN;
TRUNCATE "organization_organizationrole", "socialaccount_socialtoken", "tutelary_role", "accounts_user_user_permissions", "tutelary_policy", "accounts_user_groups", "authtoken_token", "tutelary_permissionset_users", "accounts_user", "organization_project", "organization_organization", "organization_projectrole", "account_emailconfirmation", "auth_group_permissions", "tutelary_roleauditlogentry", "socialaccount_socialapp", "django_session", "socialaccount_socialapp_sites", "tutelary_permissionset", "auth_group", "tutelary_policyauditlogentry", "account_emailaddress", "tutelary_policyinstance", "tutelary_rolepolicyassign", "auth_permission", "socialaccount_socialaccount";
SELECT setval(pg_get_serial_sequence('"auth_permission"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"auth_group"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"accounts_user"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"tutelary_policyauditlogentry"','action_id'), 1, false);
SELECT setval(pg_get_serial_sequence('"tutelary_policy"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"tutelary_rolepolicyassign"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"tutelary_roleauditlogentry"','action_id'), 1, false);
SELECT setval(pg_get_serial_sequence('"tutelary_role"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"tutelary_policyinstance"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"tutelary_permissionset"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"account_emailaddress"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"account_emailconfirmation"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"socialaccount_socialapp"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"socialaccount_socialaccount"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"socialaccount_socialtoken"','id'), 1, false);

COMMIT;
