import { useMutation, useQueryClient } from '@tanstack/react-query';
import { calculatePayroll } from '../api/calculatePayroll';
import { payrollKeys } from './usePayrollData';

export function useCalculateSalary() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: calculatePayroll,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: payrollKeys.all }),
  });
}
