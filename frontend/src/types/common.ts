export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
}

export interface SelectOption<T = string> {
  label: string;
  value: T;
}

export interface ApiError {
  message: string;
  code?: string;
}
