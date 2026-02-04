export class APIError extends Error {
  status: number;
  data: any;

  constructor(message: string, status: number, data?: any) {
    super(message);
    this.name = 'APIError';
    this.status = status;
    this.data = data;
  }
}

const errorMessages: Record<number, string> = {
  400: 'Requisição inválida. Verifique os dados enviados.',
  401: 'Você não está autenticado. Faça login novamente.',
  403: 'Você não tem permissão para acessar este recurso.',
  404: 'Recurso não encontrado.',
  409: 'Conflito. O recurso já existe ou está em uso.',
  422: 'Dados inválidos. Verifique os campos e tente novamente.',
  429: 'Muitas requisições. Tente novamente em alguns instantes.',
  500: 'Erro no servidor. Tente novamente mais tarde.',
  502: 'Serviço temporariamente indisponível.',
  503: 'Serviço em manutenção. Tente novamente em breve.',
};

export function handleAPIError(error: any): APIError {
  // Network error
  if (!error.response && error instanceof TypeError) {
    return new APIError(
      'Erro de conexão. Verifique sua internet e tente novamente.',
      0
    );
  }

  // API error with response
  if (error.response) {
    const status = error.response.status;
    const data = error.response.data;

    // Use custom message from API if available
    const message = data?.message || data?.detail || errorMessages[status] || 'Erro desconhecido.';

    return new APIError(message, status, data);
  }

  // Generic error
  return new APIError(
    error.message || 'Ocorreu um erro inesperado.',
    500
  );
}

export function isNetworkError(error: any): boolean {
  return error instanceof APIError && error.status === 0;
}

export function isAuthError(error: any): boolean {
  return error instanceof APIError && (error.status === 401 || error.status === 403);
}

export function isServerError(error: any): boolean {
  return error instanceof APIError && error.status >= 500;
}
