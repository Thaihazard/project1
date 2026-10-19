import { useAuthStore } from '@/store/useAuthStore';

interface CanProps {
  perform: string;
  children: React.ReactNode;
}

export const Can = ({ perform, children }: CanProps) => {
  const { user } = useAuthStore();
  const permissions = user?.permissions || [];

  if (permissions.includes(perform)) {
    return <>{children}</>;
  }

  return null;
};
