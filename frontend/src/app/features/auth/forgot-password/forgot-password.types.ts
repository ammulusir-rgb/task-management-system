/**
 * Forgot Password component types and i18n keys
 */
export interface ForgotPasswordFormValue {
  email: string;
}

export interface ForgotPasswordI18nKeys {
  title: string;
  subtitle: string;
  sendResetLink: string;
  resetSent: string;
  backToSignIn: string;
}

export const FORGOT_PASSWORD_I18N_KEYS: ForgotPasswordI18nKeys = {
  title: 'auth.forgotPasswordTitle',
  subtitle: 'auth.forgotPasswordSubtitle',
  sendResetLink: 'auth.sendResetLink',
  resetSent: 'auth.resetSent',
  backToSignIn: 'auth.backToSignIn',
};
