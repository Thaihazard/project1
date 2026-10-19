export const formatVnd = (amount: number) =>
  `${new Intl.NumberFormat('vi-VN').format(amount)} VNĐ`;
