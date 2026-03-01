/**
 * Confirm Dialog component types and i18n keys
 */
export interface ConfirmDialogConfig {
  title: string;
  message: string;
  confirmText: string;
  cancelText: string;
  confirmClass: string;
}

export interface ConfirmDialogI18nKeys {
  defaultTitle: string;
  defaultMessage: string;
  confirm: string;
  cancel: string;
}

export const CONFIRM_DIALOG_I18N_KEYS: ConfirmDialogI18nKeys = {
  defaultTitle: 'confirm.title',
  defaultMessage: 'confirm.message',
  confirm: 'confirm.confirm',
  cancel: 'confirm.cancel',
};
