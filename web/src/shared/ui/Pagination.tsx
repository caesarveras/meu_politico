type PaginationProps = {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
};

function buildVisiblePages(currentPage: number, totalPages: number) {
  if (totalPages <= 5) {
    return Array.from({ length: totalPages }, (_, index) => index + 1);
  }

  const pages = new Set<number>([1, totalPages, currentPage]);
  if (currentPage > 1) pages.add(currentPage - 1);
  if (currentPage < totalPages) pages.add(currentPage + 1);
  if (currentPage <= 2) pages.add(3);
  if (currentPage >= totalPages - 1) pages.add(totalPages - 2);
  return Array.from(pages).sort((left, right) => left - right);
}

export function Pagination({ currentPage, totalPages, onPageChange }: PaginationProps) {
  if (totalPages <= 1) {
    return null;
  }

  const visiblePages = buildVisiblePages(currentPage, totalPages);

  return (
    <nav aria-label="Paginação" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
      <button type="button" onClick={() => onPageChange(Math.max(1, currentPage - 1))} disabled={currentPage === 1} style={{ minHeight: '40px', minWidth: '40px', padding: '0 12px', borderRadius: '999px', border: '1px solid #D7DEE5', background: '#FFFFFF', color: '#16202A' }}>
        Anterior
      </button>
      {visiblePages.map((page, index) => {
        const previousPage = visiblePages[index - 1];
        const showEllipsis = previousPage && page - previousPage > 1;
        return (
          <span key={`page-${page}`} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            {showEllipsis ? <span style={{ color: '#5C6B7A' }}>…</span> : null}
            <button
              type="button"
              onClick={() => onPageChange(page)}
              aria-current={page === currentPage ? 'page' : undefined}
              style={{
                minHeight: '40px',
                minWidth: '40px',
                padding: '0 12px',
                borderRadius: '999px',
                border: `1px solid ${page === currentPage ? '#0F4C81' : '#D7DEE5'}`,
                background: page === currentPage ? '#0F4C81' : '#FFFFFF',
                color: page === currentPage ? '#FFFFFF' : '#16202A',
                fontWeight: page === currentPage ? 700 : 500,
              }}
            >
              {page}
            </button>
          </span>
        );
      })}
      <button type="button" onClick={() => onPageChange(Math.min(totalPages, currentPage + 1))} disabled={currentPage === totalPages} style={{ minHeight: '40px', minWidth: '40px', padding: '0 12px', borderRadius: '999px', border: '1px solid #D7DEE5', background: '#FFFFFF', color: '#16202A' }}>
        Próxima
      </button>
    </nav>
  );
}
