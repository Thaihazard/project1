"""PDF output is an optional integration point; payslip exports currently use XLSX."""


def generate_payslip_pdf(*_args, **_kwargs) -> bytes:
    raise NotImplementedError("Configure a PDF renderer before enabling payslip PDF downloads")
