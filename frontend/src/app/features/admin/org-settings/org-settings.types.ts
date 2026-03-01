/**
 * Org Settings component types and i18n keys
 */
export interface OrgSettingsI18nKeys {
  orgSettings: string;
  orgName: string;
  description: string;
  manageMembers: string;
  saved: string;
  saveFailed: string;
}

export const ORG_SETTINGS_I18N_KEYS: OrgSettingsI18nKeys = {
  orgSettings: 'admin.orgSettings',
  orgName: 'admin.orgName',
  description: 'admin.description',
  manageMembers: 'admin.manageMembers',
  saved: 'admin.settingsSaved',
  saveFailed: 'admin.saveFailed',
};
