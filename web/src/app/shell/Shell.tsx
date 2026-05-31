import { useContext, useEffect, useMemo } from 'react';
import { Link, NavLink, Outlet, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

import { Locale, LocaleContext } from '../providers/AppProviders';
import { AppShellStyles } from './Shell.styles';

const locales: Array<{ key: Locale; label: string }> = [
  { key: 'pt-BR', label: 'PT' },
  { key: 'es', label: 'ES' },
  { key: 'en', label: 'EN' },
];

type BreadcrumbItem = {
  label: string;
  to?: string;
};

export function Shell() {
  const { t } = useTranslation();
  const { locale, setLocale } = useContext(LocaleContext);
  const location = useLocation();

  useEffect(() => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, [location.pathname]);

  const getNavLinkStyle = ({ isActive }: { isActive: boolean }) => (isActive ? AppShellStyles.navLinkActive : AppShellStyles.navLink);
  const breadcrumbItems = useMemo(() => {
    const items: BreadcrumbItem[] = [{ label: t('shell.home'), to: '/' }];

    if (location.pathname === '/') {
      return items;
    }

    if (location.pathname === '/leis') {
      items.push({ label: t('shell.bills'), to: '/leis' });
      return items;
    }

    if (location.pathname.startsWith('/leis-aprovadas')) {
      items.push({ label: t('shell.approvedBills'), to: '/leis-aprovadas' });
      return items;
    }

    if (location.pathname.startsWith('/leis/')) {
      items.push({ label: t('shell.bills'), to: '/leis' });
      items.push({ label: t('shell.billDetail') });
      return items;
    }

    if (location.pathname.startsWith('/parlamentares')) {
      items.push({ label: t('shell.politicians'), to: '/parlamentares' });
      return items;
    }

    if (location.pathname.startsWith('/politicos/')) {
      items.push({ label: t('shell.politicians'), to: '/parlamentares' });
      items.push({ label: t('shell.politicianDetail') });
      return items;
    }

    return items;
  }, [location.pathname, t]);

  return (
    <div style={AppShellStyles.page} data-testid="app-shell">
      <header style={AppShellStyles.header} data-testid="app-header">
        <div style={AppShellStyles.brandColumn}>
          <p style={AppShellStyles.eyebrow}>{t('shell.eyebrow')}</p>
          <h1 style={AppShellStyles.brand}>{t('shell.brand')}</h1>
          <p style={AppShellStyles.subtitle}>{t('shell.subtitle')}</p>
          <p style={AppShellStyles.mission} data-testid="public-mission-text">{t('shell.mission')}</p>
        </div>

        <div style={AppShellStyles.actions}>
          <nav style={AppShellStyles.nav} data-testid="main-nav" aria-label={t('shell.navLabel')}>
            <NavLink to="/" style={getNavLinkStyle} data-testid="nav-home">{t('shell.home')}</NavLink>
            <NavLink to="/leis" style={getNavLinkStyle} data-testid="nav-bills">{t('shell.bills')}</NavLink>
            <NavLink to="/leis-aprovadas" style={getNavLinkStyle} data-testid="nav-approved-bills">{t('shell.approvedBills')}</NavLink>
            <NavLink to="/parlamentares" style={getNavLinkStyle} data-testid="nav-politicians">{t('shell.politicians')}</NavLink>
          </nav>
          <div style={AppShellStyles.localeRow} data-testid="locale-switcher">
            {locales.map((item) => (
              <button
                key={item.key}
                type="button"
                onClick={() => setLocale(item.key)}
                style={locale === item.key ? AppShellStyles.localeButtonActive : AppShellStyles.localeButton}
                data-testid={`locale-${item.key}`}
              >
                {item.label}
              </button>
            ))}
          </div>
        </div>
      </header>

      {breadcrumbItems.length > 1 ? (
        <div style={AppShellStyles.breadcrumbWrapper}>
          <nav style={AppShellStyles.breadcrumbNav} aria-label={t('shell.breadcrumbLabel')} data-testid="app-breadcrumb">
            {breadcrumbItems.map((item, index) => {
              const isLast = index === breadcrumbItems.length - 1;
              const itemKey = `${item.label}-${item.to ?? index}`;
              return (
                <span key={itemKey} style={AppShellStyles.breadcrumbNav}>
                  {item.to && !isLast ? (
                    <Link to={item.to} style={AppShellStyles.breadcrumbLink}>{item.label}</Link>
                  ) : (
                    <span style={isLast ? AppShellStyles.breadcrumbCurrent : AppShellStyles.breadcrumbLink}>{item.label}</span>
                  )}
                  {!isLast ? <span style={AppShellStyles.breadcrumbSeparator}>/</span> : null}
                </span>
              );
            })}
          </nav>
        </div>
      ) : null}

      <main style={AppShellStyles.main} data-testid="app-main">
        <Outlet />
      </main>

      <footer style={AppShellStyles.footer} data-testid="app-footer">
        <div style={AppShellStyles.footerGrid}>
          <div>
            <h2 style={AppShellStyles.footerTitle}>{t('shell.footerTitle')}</h2>
            <p style={AppShellStyles.footerText}>{t('shell.footerBody')}</p>
            <p style={AppShellStyles.footerText}>{t('shell.footerLicense')}</p>
          </div>
          <div style={AppShellStyles.footerMeta}>
            <p style={AppShellStyles.footerMetaText}>{t('shell.footerTransparency')}</p>
            <p style={AppShellStyles.footerMetaText}>{t('shell.footerCoverage')}</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
