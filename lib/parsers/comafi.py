import streamlit as st
from typing import List, Dict
import re

class ComafiParser:
    def parse(self, data: List[str]) -> List[Dict[str, str]]:
        transactions = []
        currency_regex = re.compile(r'(\d{1,3}(?:\.\d{3})*,\d{2})')  # Matches numbers like 1.234,56

        for page_number, page in enumerate(data, start=1):
            lines = page.split('\n')
            try:
                # Locate the "DETALLE DE MOVIMIENTOS" section
                detalle_idx = next(i for i, line in enumerate(lines) if "DETALLE DE MOVIMIENTOS" in line)
            except StopIteration:
                st.warning(f"Page {page_number}: 'DETALLE DE MOVIMIENTOS' section not found.")
                continue  # Skip this page if the section is not found

            # Find the header line after "DETALLE DE MOVIMIENTOS"
            header_line = None
            header_idx = detalle_idx
            for i in range(detalle_idx, len(lines)):
                if all(col in lines[i] for col in ["Fecha", "Conceptos", "Referencias", "Débitos", "Créditos", "Saldo"]):
                    header_line = lines[i]
                    header_idx = i
                    break

            if not header_line:
                st.warning(f"Page {page_number}: Header line not found after 'DETALLE DE MOVIMIENTOS'.")
                continue  # Skip if header is not found

            # Determine the start index of each column based on the header line
            col_positions = {}
            columns = ["Fecha", "Conceptos", "Referencias", "Débitos", "Créditos", "Saldo"]
            for col in columns:
                start = header_line.find(col)
                if start != -1:
                    col_positions[col] = start

            # Ensure all columns were found
            if len(col_positions) != len(columns):
                st.warning(f"Page {page_number}: Not all columns found in the header.")
                continue  # Skip if any column is missing

            # Sort columns by their start position
            sorted_cols = sorted(col_positions.items(), key=lambda x: x[1])

            # Determine the boundaries for each column
            col_boundaries = {}
            for i, (col, start) in enumerate(sorted_cols):
                if i < len(sorted_cols) - 1:
                    end = sorted_cols[i + 1][1]
                else:
                    end = None  # Last column goes till the end
                col_boundaries[col] = (start, end)

            # Process each line after the header until "Saldo al" is found
            for line in lines[header_idx + 1:]:
                if "Saldo al" in line:
                    # Extract the Saldo value
                    saldo_match = currency_regex.search(line)
                    saldo = saldo_match.group(1) if saldo_match else ""
                    
                    # Extract the date from "Saldo al: dd/mm/yyyy"
                    date_match = re.search(r"Saldo al:\s*(\d{1,2}/\d{1,2}/\d{2,4})", line)
                    fecha = date_match.group(1) if date_match else ""
                    
                    transaction = {
                        "Fecha": fecha,
                        "Conceptos": "Saldo",
                        "Referencias": "",
                        "Débitos": "",
                        "Créditos": "",
                        "Saldo": saldo
                    }
                    transactions.append(transaction)
                    break  # End of transactions for this section

                if not line.strip():
                    continue  # Skip empty lines

                # Extract fields based on column boundaries
                transaction = {}
                for col in columns:
                    start, end = col_boundaries[col]
                    if end:
                        field = line[start:end].strip()
                    else:
                        field = line[start:].strip()
                    transaction[col] = field

                # Handle the last three columns which are right-aligned numbers
                # They might not align perfectly, so use regex to extract them
                debito_match = currency_regex.search(transaction["Débitos"])
                credito_match = currency_regex.search(transaction["Créditos"])
                saldo_match = currency_regex.search(transaction["Saldo"])

                transaction["Débitos"] = debito_match.group(1) if debito_match else ""
                transaction["Créditos"] = credito_match.group(1) if credito_match else ""
                transaction["Saldo"] = saldo_match.group(1) if saldo_match else ""

                # Clean and standardize the data (e.g., convert numbers to float)
                for key in ["Débitos", "Créditos", "Saldo"]:
                    value = transaction[key]
                    if value:
                        # Replace dots with empty string and commas with dots for decimal
                        value_clean = value.replace('.', '').replace(',', '.')
                        try:
                            transaction[key] = float(value_clean)
                        except ValueError:
                            transaction[key] = value_clean  # Keep as string if conversion fails

                # Append to transactions if at least Fecha or Saldo is present
                if transaction["Fecha"] or transaction["Saldo"]:
                    transactions.append(transaction)

        # Optionally, display the transactions in Streamlit
        st.write(f"Total transactions extracted: {len(transactions)}")
        st.dataframe(transactions)

        return transactions



sample_input_data = [
  "Los depósitos en pesos y en moneda extranjera cuentan con la garantía de hasta $ 1.500.000.- En las operaciones a nombre de dos ó más personas, la garantía se prorrateará entre sus titulares.  En ningún caso, el total de la garantía por\npersona y por depósito podrá exceder de $1.500.000, cualquiera sea el número de cuentas y/o depósitos. Ley 24.485, Decreto 540/95 y modificatorios y Com. \"A\" 2337 y sus modificatorias y complementarias. Se encuentran excluidos los \ncaptados a tasas superiores a la de referencia conforme a los límites establecidos por el Banco Central, los adquiridos por endoso y  los efectuados por personas vinculadas a la entidad financiera. \n\"Se ruega formular por escrito o personalmente  las  observaciones  a  este  extracto en  la  sucursal  de radicación  de  la  cuenta,  dentro  de  los 60 días  corridos  de  vencido  el  período.  En  caso  contrario se presumirá conformidad \nEl Impuesto al Valor Agregado discriminado no podrá ser computado como crédito fiscal si su condición frente a este impuesto es distinta a la de Responsable Inscripto.\n  (Circular OPASi 2 BCRA).\"\n                                                     Comafi Empresas Classic                       \n                                                                                            RESUMEN DE OPERACIONES                  \n                                                                                            ENERO - 2023                            \n                                                                                            Emision : Mensual                       \n                   81.477 - 1/2       - 12                                                                                          \n                  SERVICIOS Y SOLUCIONES INT SA                                                    Hoja:1/2                         \n                  Avenida Acceso Sur 4389                                                          Secuencia : 16                   \n                                                                                                   Código:E                         \n                  5507       Lujan De Cuyo                                                         CUIT 30710922973                 \n                  Mendoza                               Suc:171                                                                     \n001710000601\n  __________________________________________________________________________________________________________________________________\n  NOTICIAS                                                                                                                          \n  Te recordamos que cuando la contratación de un servicio, incluídos los servicios públicos                                         \n  domiciliarios, haya sido realizada en forma telefónica, electrónica o similar, podrá ser rescindida                               \n  a elección del consumidor o usuario mediante el mismo medio utilizado en la contratación. La empresa                              \n  receptora del pedido de rescisión del servicio deberá enviar sin cargo al domicilio del consumidor                                \n  o usuario una constancia fehaciente dentro de las SETENTA Y DOS (72) horas posteriores a la                                       \n  recepción del pedido de rescisión (Ley 26.361 - Art. 10° ter).                                                                    \n  El titular de los datos personales tiene la facultad de ejercer el derecho de acceso a los mismos en                              \n  forma gratuita a intervalos no inferiores a seis meses, salvo que se acredite un interés legítimo al                              \n  efecto conforme lo establecido en el artículo 14, inciso 3 de la Ley Nº25.326. La DIRECCION                                       \n  NACIONAL DE PROTECCION DE DATOS PERSONALES, Órgano de Control de la Ley Nº25.326, tiene la                                        \n  atribución de atender las denuncias y reclamos que se interpongan con relación al incumplimiento                                  \n  de las normas sobre protección de datos personales. El titular podrá en cualquier momento solicitar                               \n  el retiro o bloqueo de su nombre de los bancos de datos y/o el responsable o usuario que proveyó la                               \n  información.                                                                                                                      \n  A los efectos del debido cumplimiento a la Resol. 52/2012 de la Unidad de Información Financiera                                  \n  respecto a la identificación de las Personas Expuestas Políticamente (PEPS), te solicitamos                                       \n  tengas a bien acercarte a tu sucursal en caso de que seas o hayas sido funcionario/s público tanto                                \n  nacional como extranjero con la finalidad de explicarte la normativa vigente y cumplimentar los                                   \n  pasos correspondientes.                                                                                                           \n  Podés consultar el \"Régimen de Transparencia\" elaborado por el Banco Central sobre la base de la                                  \n  información proporcionada por los sujetos obligados a fin de comparar los costos, características                                 \n  y requisitos de los productos y servicios financieros, ingresando a                                                               \n  http://www.bcra.gob.ar/BCRAyVos/Regimen_de_transparencia.asp                                                                      \n  IMPORTANTE: Tené presente que si efectuas transacciones en cajeros automáticos de otras redes                                     \n  distintas de Banelco en el país, las mismas, independientemente de las comisiones que te cobremos                                 \n  por su uso, podrían estar alcanzadas por un costo extra que genera y te cobra el administrador de                                 \n  dicha red de manera directa realizando un débito en tu cuenta. Este costo te lo informará                                         \n  previamente el cajero automático antes de confirmar la transacción para que puedas decidir                                        \n  realizarla o no. Esos costos no son cobrados por Banco Comafi ni tiene injerencia alguna en los                                   \n  mismos. Recordá que tenés a disposición la red Banelco y Link para realizar las operaciones sin                                   \n  costo adicional al que percibe el Banco.                                                                                          \n  Te informamos que conforme las reglamentaciones de los Mercados y Resolución de la Comisión                                       \n  Nacional de Valores (CNV) 731/2018 la documentación de respaldo de cada operación se encuentra a                                  \n  tu disposición.                                                                                                                   \n  Comafi Token Empresas y Código SMS son los medios que deben utilizar todos los autorizantes                                       \n  de eBanking Empresas para aprobar las operaciones realizadas en dicho canal. Comafi Token                                         \n  Empresas está disponible en 2 soluciones: para celulares y computadoras. Para más información                                     \n  sobre adhesiones y uso, ingresá a www.comafi.com.ar o contactate con nuestro Centro de Atención                                   \n  a Empresas.                                                                                                                       \n  Para realizar consultas, denunciar delitos informáticos o anunciar alguna situación en particular,                                \n  podés comunicarte con nuestro Centro de Atención a Empresas telefónicamente al 0810-122-6622                                      \n  de lunes a viernes en el horario de 9 a 18hs o vía mail a comafiempresas@comafi.com.ar.                                           \n  Te informamos que la Oficina de Defensa al Consumidor en Lujan de Cuyo atiende en los siguientes                                  \n  teléfonos: (0261) 4984226                                                                                                         \n",
  "Los depósitos en pesos y en moneda extranjera cuentan con la garantía de hasta $ 1.500.000.- En las operaciones a nombre de dos ó más personas, la garantía se prorrateará entre sus titulares.  En ningún caso, el total de la garantía por\npersona y por depósito podrá exceder de $1.500.000, cualquiera sea el número de cuentas y/o depósitos. Ley 24.485, Decreto 540/95 y modificatorios y Com. \"A\" 2337 y sus modificatorias y complementarias. Se encuentran excluidos los \ncaptados a tasas superiores a la de referencia conforme a los límites establecidos por el Banco Central, los adquiridos por endoso y  los efectuados por personas vinculadas a la entidad financiera. \n\"Se ruega formular por escrito o personalmente  las  observaciones  a  este  extracto en  la  sucursal  de radicación  de  la  cuenta,  dentro  de  los 60 días  corridos  de  vencido  el  período.  En  caso  contrario se presumirá conformidad \nEl Impuesto al Valor Agregado discriminado no podrá ser computado como crédito fiscal si su condición frente a este impuesto es distinta a la de Responsable Inscripto.\n  (Circular OPASi 2 BCRA).\"\n  COMAFI EMPRESAS CLASSIC              Nro 0889226       Sucursal: Lujan De Cuyo - Mendoza            .                             \n  ----------------------------------------------------------------------------------------------------------------------------------\n  TITULAR                                                       CUIT                                     SITUACIÓN IMPOSITIVA       \n  ----------------------------------------------------------------------------------------------------------------------------------\n    SERVICIOS Y SOLUCIONES INT SA                               30-71092297-3                            Responsable Inscripto      \n  ----------------------------------------------------------------------------------------------------------------------------------\n  Productos COMAFI EMPRESAS CLASSIC         Número de Cuenta/Tarjeta   Moneda      Límite de Crédito                   Saldo        \n  ----------------------------------------------------------------------------------------------------------------------------------\n  Cuenta Corriente Bancaria                   1710-00060-1             Pesos                 0,00                     2.239.979,46  \n  Cuenta Corriente Especial                   1711-00233-0             Pesos                 0,00                             0,00  \n  Cuenta Corriente Especial                   1711-00234-7             Dolares               0,00                             0,00  \n                                                                              Total Pesos:                            2.239.979,46  \n  COMAFI EMPRESAS CLASSIC           CUENTA CORRIENTE BANCARIA EN PESOS                                .                             \n    Número 1710-00060-1                             CBU: 2990171317100006010002                                                     \n  ----------------------------------------------------------------------------------------------------------------------------------\n  DETALLE DE MOVIMIENTOS                                                                                                            \n  ----------------------------------------------------------------------------------------------------------------------------------\n   Fecha   Conceptos                          Referencias                                Débitos       Créditos              Saldo  \n  31/12/22                                                       Saldo Anterior                                        2.246.170,50 \n  03/01/23 Impuesto a los debitos - tasa gene 0012745                                        0,89                                   \n  03/01/23 Impuesto a los debitos - tasa gene 0012745                                        6,25                                   \n  03/01/23 Impuesto a los debitos - tasa gene 0012745                                       29,78                                   \n  03/01/23 Percepcion IVA RG 2408             0012745                                      148,89                                   \n  03/01/23 IVA - Alicuota General             0012745                                    1.042,23                                   \n  03/01/23 Comisión Mantenimiento Servicio Cu 0012745                                    4.963,00                      2.239.979,46 \n                                                                  Saldo al: 31/01/2023                                 2.239.979,46 \n  ----------------------------------------------------------------------------------------------------------------------------------\n  IMPUESTOS DEBITADOS EN EL PERIODO        Cuenta Corriente Bancaria Nro. 1710-00060-1                                              \n  ----------------------------------------------------------------------------------------------------------------------------------\n                                                        Base Imponible  Alícuota       Debitado    Devoluciones          Neto       \n  Ley 25413 Sobre  Débitos  Tasa general                      6.154,12   0,600%           36,92            0,00           36,92     \n  TOTAL AL: 31/01/23                                                                      36,92            0,00           36,92 (1) \n  (1)Total Pago a Cuenta Artículo 13 - Anexo Decreto 380/1: al 31/01/23           $ 12,18                                           \n  El importe discriminado es a sólo efecto de dar cumplimiento con lo establecido por la RG(AFIP) 1788/2004, debiendo el titular    \n  de la cuenta realizar los cálculos que correspondan a fin de determinar el pago a cuenta que resulte computable.                  \n  COMAFI EMPRESAS CLASSIC           CUENTA CORRIENTE ESPECIAL EN PESOS                                .                             \n    NRO. 1711-00233-0                               CBU: 2990171317110023300017                                                     \n  ----------------------------------------------------------------------------------------------------------------------------------\n  DETALLE DE MOVIMIENTOS                                                                                                            \n  ----------------------------------------------------------------------------------------------------------------------------------\n   Fecha   Conceptos                          Referencias                                Débitos       Créditos              Saldo  \n  31/12/22                                                       Saldo Anterior                                                0,00 \n                                                           SIN MOVIMIENTOS                                                          \n                                                                  Saldo al: 31/01/2023                                         0,00 \n  COMAFI EMPRESAS CLASSIC           CUENTA CORRIENTE ESPECIAL EN DOLARES                              .                             \n    NRO. 1711-00234-7                               CBU: 2990171317110023470219                                                     \n",
  "Los depósitos en pesos y en moneda extranjera cuentan con la garantía de hasta $ 1.500.000.- En las operaciones a nombre de dos ó más personas, la garantía se prorrateará entre sus titulares.  En ningún caso, el total de la garantía por\npersona y por depósito podrá exceder de $1.500.000, cualquiera sea el número de cuentas y/o depósitos. Ley 24.485, Decreto 540/95 y modificatorios y Com. \"A\" 2337 y sus modificatorias y complementarias. Se encuentran excluidos los \ncaptados a tasas superiores a la de referencia conforme a los límites establecidos por el Banco Central, los adquiridos por endoso y  los efectuados por personas vinculadas a la entidad financiera. \n\"Se ruega formular por escrito o personalmente  las  observaciones  a  este  extracto en  la  sucursal  de radicación  de  la  cuenta,  dentro  de  los 60 días  corridos  de  vencido  el  período.  En  caso  contrario se presumirá conformidad \nEl Impuesto al Valor Agregado discriminado no podrá ser computado como crédito fiscal si su condición frente a este impuesto es distinta a la de Responsable Inscripto.\n  (Circular OPASi 2 BCRA).\"\n   81.477 - 2/2       - 12                                                SERVICIOS Y SOLUCIONES INT SA                             \n                                                                          Hoja:2/2                                                  \n  ----------------------------------------------------------------------------------------------------------------------------------\n  DETALLE DE MOVIMIENTOS                                                                                                            \n  ----------------------------------------------------------------------------------------------------------------------------------\n   Fecha   Conceptos                          Referencias                                Débitos       Créditos              Saldo  \n  31/12/22                                                       Saldo Anterior                                                0,00 \n                                                           SIN MOVIMIENTOS                                                          \n                                                                  Saldo al: 31/01/2023                                         0,00 \n  ----------------------------------------------------------------------------------------------------------------------------------\n"
]


expected_data = [
    {
        "Fecha": "31/12/22",
        "Conceptos": "Saldo Anterior",
        "Referencias": "",
        "Débitos": "",
        "Créditos": "",
        "Saldo": "2.246.170,50"
    },
    {
        "Fecha": "03/01/23",
        "Conceptos": "Impuesto a los debitos - tasa gene",
        "Referencias": "0012745",
        "Débitos": "0,89",
        "Créditos": "",
        "Saldo": ""
    },
    {
        "Fecha": "03/01/23",
        "Conceptos": "Impuesto a los debitos - tasa gene",
        "Referencias": "0012745",
        "Débitos": "6,25",
        "Créditos": "",
        "Saldo": ""
    },
    {
        "Fecha": "03/01/23",
        "Conceptos": "Impuesto a los debitos - tasa gene",
        "Referencias": "0012745",
        "Débitos": "29,78",
        "Créditos": "",
        "Saldo": ""
    },
    {
        "Fecha": "03/01/23",
        "Conceptos": "Percepcion IVA RG 2408",
        "Referencias": "0012745",
        "Débitos": "148,89",
        "Créditos": "",
        "Saldo": ""
    },
    {
        "Fecha": "03/01/23",
        "Conceptos": "IVA - Alicuota General",
        "Referencias": "0012745",
        "Débitos": "1.042,23",
        "Créditos": "",
        "Saldo": ""
    },
    {
        "Fecha": "03/01/23",
        "Conceptos": "Comisión Mantenimiento Servicio Cu",
        "Referencias": "0012745",
        "Débitos": "4.963,00",
        "Créditos": "",
        "Saldo": "2.239.979,46"
    },
    {
        "Fecha": "31/01/23",
        "Conceptos": "Saldo",
        "Referencias": "",
        "Débitos": "",
        "Créditos": "",
        "Saldo": "2.239.979,46"
    }
]