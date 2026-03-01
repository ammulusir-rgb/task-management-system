/**
 * Login component types and i18n keys
 */
export interface LoginFormValue {
  email: string;
  password: string;
}

export interface LoginI18nKeys {
  welcomeBack: string;
  signInSubtitle: string;
  email: string;
  emailPlaceholder: string;
  emailRequired: string;
  password: string;
  passwordPlaceholder: string;
  rememberMe: string;
  forgotPassword: string;
  signIn: string;
  noAccount: string;
  signUp: string;
}

export const LOGIN_I18N_KEYS: LoginI18nKeys = {
  welcomeBack: 'auth.welcomeBack',
  signInSubtitle: 'auth.signInSubtitle',
  email: 'auth.email',
  emailPlaceholder: 'auth.emailPlaceholder',
  emailRequired: 'auth.emailRequired',
  password: 'auth.password',
  passwordPlaceholder: 'auth.passwordPlaceholder',
  rememberMe: 'auth.rememberMe',
  forgotPassword: 'auth.forgotPassword',
  signIn: 'auth.signIn',
  noAccount: 'auth.noAccount',
  signUp: 'auth.signUp',
};
