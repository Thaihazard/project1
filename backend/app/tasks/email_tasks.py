from app.core.celery_app import celery_app

if celery_app is not None:
    @celery_app.task(name="email.send_payslip_notice")
    def send_payslip_notice(recipient: str, employee_name: str, pay_period: str) -> dict[str, str]:
        # Configure an SMTP provider before enabling delivery of employee salary data.
        return {"status": "not_configured", "recipient": recipient, "employee": employee_name, "payPeriod": pay_period}
else:
    def send_payslip_notice(recipient: str, employee_name: str, pay_period: str) -> dict[str, str]:
        raise RuntimeError("Install celery[redis] to run email background tasks")
