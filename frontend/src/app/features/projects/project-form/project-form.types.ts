/**
 * Project Form component types and i18n keys
 */
export interface ProjectFormValue {
  name: string;
  prefix: string;
  organization: string;
  description: string;
}

export interface ProjectFormI18nKeys {
  editTitle: string;
  createTitle: string;
  organization: string;
  selectOrg: string;
  name: string;
  namePlaceholder: string;
  prefix: string;
  prefixHint: string;
  description: string;
  descriptionPlaceholder: string;
  update: string;
  create: string;
  updated: string;
  created: string;
}

export const PROJECT_FORM_I18N_KEYS: ProjectFormI18nKeys = {
  editTitle: 'projectForm.editTitle',
  createTitle: 'projectForm.createTitle',
  organization: 'projectForm.organization',
  selectOrg: 'projectForm.selectOrg',
  name: 'projectForm.name',
  namePlaceholder: 'projectForm.namePlaceholder',
  prefix: 'projectForm.prefix',
  prefixHint: 'projectForm.prefixHint',
  description: 'projectForm.description',
  descriptionPlaceholder: 'projectForm.descriptionPlaceholder',
  update: 'projectForm.update',
  create: 'projectForm.create',
  updated: 'projectForm.updated',
  created: 'projectForm.created',
};
