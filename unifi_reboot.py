from unificontrol import UnifiClient
import ssl
import json
import time

def fetch_ssl_certificate(controller_url, port):
    try:
        return ssl.get_server_certificate((controller_url, port))
    except Exception as e:
        print(f"Failed to fetch SSL certificate: {e}")
        return None

def get_sites(controller_url, username, password, port, cert):
    client = UnifiClient(host=controller_url, username=username, password=password, port=port, cert=cert)

    try:
        sites = client.list_sites()
        site_names = [site.get('name') for site in sites if 'name' in site]
        
        with open('site_names.json', 'w', encoding='utf-8') as f:
            json.dump(site_names, f, ensure_ascii=False, indent=4)
        
        print("Список имен сайтов успешно сохранен в файл 'site_names.json'")
        return site_names
    except Exception as e:
        print(f"Failed to fetch sites: {e}")
        return []

def get_devices(controller_url, username, password, port, site, cert):
    client = UnifiClient(host=controller_url, username=username, password=password, port=port, site=site, cert=cert)

    try:
        devices = client.list_devices()
        devices_info = [{'ip': device.get('ip'), 'mac': device.get('mac', 'N/A'), 'uptime': device.get('uptime'), 'model': device.get('model', 'N/A')} for device in devices]
        
        with open(f'devices_{site}.json', 'w', encoding='utf-8') as f:
            json.dump(devices_info, f, ensure_ascii=False, indent=4)
        
        print(f"Информация об устройствах для сайта {site} успешно сохранена в файл 'devices_{site}.json'")
        return devices_info
    except Exception as e:
        print(f"Failed to fetch devices for site {site}: {e}")
        return []

def check_and_reboot_devices(controller_url, username, password, port, site, devices_info, cert):
    client = UnifiClient(host=controller_url, username=username, password=password, port=port, site=site, cert=cert)
    reboot_delay_seconds = 2 * 60 #устанавливаем задержку между перезагрузками устройств
    ten_days_in_seconds = 10 * 24 * 60 * 60 #устанавливаем uptime устройств, если привышает то перезагружаем

    try:
        sites = client.list_sites()
        site_names = [site.get('desc') for site in sites if 'desc' in site]

        for device in devices_info:
            uptime = device.get('uptime')
            mac = device.get('mac', 'N/A')
            name = device.get('name', 'N/A')
            
            # Добавление исключения для определённого сайта
            if site == "":
                print(f"Для сайта {site} перезагрузка устройств не требуется.")
                continue  # Пропускаем перезагрузку устройств для этого сайта

            if uptime is not None:
                if uptime > ten_days_in_seconds:
                    print(f"Устройство {name} {mac} на сайте будет перезагружено через пару секунд. Пробуем...")
                    try:
                        client.restart_ap(mac)
                        print(f"Устройство {name} успешно перезагружено.")
                        time.sleep(reboot_delay_seconds)
                    except Exception as e:
                        print(f"Failed to reboot device {mac}: {e}")
                else:
                    print(f"Время работы устройства {name} {mac} корректно, перезагрузка не требуется.")
            else:
                print(f"Время работы устройства {name} {mac} не определено.")
    except Exception as e:
        print(f"Failed to fetch sites: {e}")

def main():
    UNIFI_HOST = "" #Без http
    UNIFI_USER = ""
    UNIFI_PASSWORD = ""
    UNIFI_PORT = 8443  # порт для unifi обычно 8443
    cert = fetch_ssl_certificate(UNIFI_HOST, UNIFI_PORT)

    sites = get_sites(UNIFI_HOST, UNIFI_USER, UNIFI_PASSWORD, UNIFI_PORT, cert)
    
    for site in sites:
        devices_info = get_devices(UNIFI_HOST, UNIFI_USER, UNIFI_PASSWORD, UNIFI_PORT, site, cert)
        if devices_info:
            check_and_reboot_devices(UNIFI_HOST, UNIFI_USER, UNIFI_PASSWORD, UNIFI_PORT, site, devices_info, cert)

if __name__ == "__main__":
    main()
