# backend/apps/utils/scrapers.py
"""
Módulo para realizar web scraping a fuentes de datos financieras.
"""

import warnings
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Dict, Optional, Union

import requests
from bs4 import BeautifulSoup

# Deshabilitar advertencias de SSL puede ser necesario para ciertos sitios,
# pero se usa con precaución.
requests.packages.urllib3.disable_warnings(
    requests.packages.urllib3.exceptions.InsecureRequestWarning
)


class BCVScraper:
    """
    Scraper robusto para obtener las tasas de cambio del Banco Central de Venezuela (BCV).

    Esta clase está diseñada para ser resiliente a cambios en el HTML, a errores
    de red y a problemas de certificados SSL, proporcionando un método limpio
    para obtener datos validados.
    """

    BCV_URL = "https://www.bcv.org.ve/"
    CURRENCY_IDS = {
        "USD": "dolar",
        "EUR": "euro",
    }

    def __init__(self):
        self._soup: Optional[BeautifulSoup] = None
        self._raw_rates: Dict[str, str] = {}
        self._effective_date_str: str = ""

    def _fetch_page(self) -> bool:
        """
        Realiza la petición HTTP y carga el contenido en BeautifulSoup.
        Intenta primero con verificación SSL y, si falla por un error de certificado,
        reintenta sin verificación, emitiendo una advertencia.

        Returns:
            bool: True si la página se cargó correctamente, False en caso contrario.
        """
        try:
            # Intento 1: Con verificación SSL (la forma segura y preferida)
            response = requests.get(self.BCV_URL, verify=True, timeout=15)
            response.raise_for_status()
            self._soup = BeautifulSoup(response.content, "html.parser")
            return True
        except requests.exceptions.SSLError as e:
            # Fallback: Si falla específicamente por SSL, reintentar sin verificación.
            warnings.warn(
                f"SSL verification failed: {e}. Retrying with verify=False. "
                "Consider updating the system's root certificates.",
                UserWarning,
            )
            try:
                # Intento 2: Sin verificación SSL
                response = requests.get(self.BCV_URL, verify=False, timeout=15)
                response.raise_for_status()
                self._soup = BeautifulSoup(response.content, "html.parser")
                return True
            except requests.exceptions.RequestException as fallback_e:
                print(f"Error fetching BCV page on fallback attempt: {fallback_e}")
                return False
        except requests.exceptions.RequestException as e:
            # Maneja otros errores de red (timeouts, 404, 500, etc.)
            print(f"Error fetching BCV page: {e}")
            return False

    def _extract_data(self):
        """
        Extrae la fecha y las tasas del objeto BeautifulSoup.
        Diseñado para fallar de forma segura si no se encuentran los elementos.
        """
        if not self._soup:
            return

        main_section = self._soup.find("div", "view-tipo-de-cambio-oficial-del-bcv")
        if not main_section:
            return

        date_tag = main_section.find("span", "date-display-single")
        if date_tag and date_tag.get("content"):
            self._effective_date_str = date_tag["content"].split("T")[0]

        for currency, tag_id in self.CURRENCY_IDS.items():
            rate_tag = main_section.find(id=tag_id)
            if rate_tag and rate_tag.find("strong"):
                rate_value = rate_tag.find("strong").text.strip().replace(",", ".")
                self._raw_rates[currency] = rate_value

    def get_processed_data(
        self,
    ) -> Optional[Dict[str, Union[datetime.date, Dict[str, Decimal]]]]:
        """
        Método principal que orquesta el scraping y devuelve datos limpios y validados.

        Returns:
            Un diccionario con la fecha efectiva y las tasas como objetos Decimal,
            o None si el proceso falla en cualquier punto crítico.
        """
        if not self._fetch_page():
            return None

        self._extract_data()

        if not self._effective_date_str or "USD" not in self._raw_rates:
            print("Failed to extract critical data (date or USD rate).")
            return None

        try:
            effective_date = datetime.strptime(
                self._effective_date_str, "%Y-%m-%d"
            ).date()
            processed_rates = {
                currency: Decimal(rate_str)
                for currency, rate_str in self._raw_rates.items()
            }
            return {"date": effective_date, "rates": processed_rates}
        except (ValueError, InvalidOperation) as e:
            print(f"Data validation failed: {e}")
            return None
