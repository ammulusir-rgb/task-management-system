/**
 * Register component types and i18n keys
 */
export interface RegisterFormValue {
  first_name: string;
  last_name: string;
  email: string;
  password: string;
  password_confirm: string;
}

export interface RegisterI18nKeys {
  createAccount: string;
  registerSubtitle: string;
  firstName: string;
  lastName: string;
  email: string;
  password: string;
  confirmPassword: string;
  minChars: string;
  passwordMinLength: string;
  passwordMismatch: string;
  createAccountBtn: string;
  haveAccount: string;
}

export const REGISTER_I18N_KEYS: RegisterI18nKeys = {
  createAccount: 'auth.createAccount',
  registerSubtitle: 'auth.registerSubtitle',
  firstName: 'auth.firstName',
  lastName: 'auth.lastName',
  email: 'auth.email',
  password: 'auth.password',
  confirmPassword: 'auth.confirmPassword',
  minChars: 'auth.minChars',
  passwordMinLength: 'auth.passwordMinLength',
  passwordMismatch: 'auth.passwordMismatch',
  createAccountBtn: 'auth.createAccountBtn',
  haveAccount: 'auth.haveAccount',
};
