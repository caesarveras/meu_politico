import { PropsWithChildren, createContext, useMemo, useState } from 'react';
import { I18nextProvider } from 'react-i18next';

import i18n from '../../i18n';

export type Locale = 'pt-BR' | 'es' | 'en';

export const LocaleContext = createContext<{
  locale: Locale;
  setLocale: (locale: Locale) => void;
}>({
  locale: 'pt-BR',
  setLocale: () => undefined,
});

export function AppProviders({ children }: PropsWithChildren) {
  const [locale, setLocaleState] = useState<Locale>('pt-BR');

  const value = useMemo(
    () => ({
      locale,
      setLocale: (nextLocale: Locale) => {
        i18n.changeLanguage(nextLocale);
        setLocaleState(nextLocale);
      },
    }),
    [locale],
  );

  return (
    <I18nextProvider i18n={i18n}>
      <LocaleContext.Provider value={value}>{children}</LocaleContext.Provider>
    </I18nextProvider>
  );
}
