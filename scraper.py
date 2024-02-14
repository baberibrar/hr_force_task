import requests
from bs4 import BeautifulSoup
import csv
import time


# Function to scrape data from a single notice
def scrape_notice(link, headers):
    response = requests.get(link, headers=headers)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        notice_summary_div = soup.find('div', class_='notice-summary')
        try:
            metadata = notice_summary_div.find('dl', class_='metadata')
        except AttributeError:
            return None

        # Extracting metadata
        metadata_values = [value.text for value in metadata.find_all('dd', class_='category')]
        metadata_values = ', '.join(metadata_values)
        notice_type = [value.text for value in metadata.find_all('dd', class_='notice-type')]
        notice_type = ', '.join(notice_type)
        notice_code = metadata.find('dd', property='gaz:hasNoticeCode').text
        notice_date = metadata.find('dd', property='gaz:hasPublicationDate').text.replace('\n', '')
        notice_id = metadata.find('dd', property='gaz:hasNoticeID').text

        # Extracting deceased details
        deceased_surname = None
        deceased_first_name = None
        address_line_1 = None
        town = None
        county = None
        additional_info = None

        deceased_content = soup.find_all('div', class_='notice-content')
        try:
            deceased_surname = deceased_content[0].find('dd', property='foaf:familyName').contents[0]
            deceased_first_name = deceased_content[0].find('dd', property='foaf:firstName').contents[0]
        except (AttributeError, IndexError):
            pass

        try:
            address_content = deceased_content[1]
            address_line_1 = address_content.find('dd', property="vcard:street-address").text
            town = address_content.find('dd', property="vcard:locality").text
            county = address_content.find('dd', property="vcard:region").text
        except (AttributeError, IndexError):
            pass

        try:
            additional_info_content = deceased_content[3]
            additional_info = additional_info_content.find('p').text
        except (AttributeError, IndexError):
            pass

        return [metadata_values, notice_type, notice_code, notice_date, notice_id,
                deceased_surname, deceased_first_name, address_line_1, town, county, additional_info]

    else:
        return None


# Main function to crawl and scrape data from pages 1 to 15
def main():
    base_url = "https://www.thegazette.co.uk/all-notices/notice?page="
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    data = []

    # Iterate over pages 1 to 15
    for page_num in range(1, 16):
        url = f"{base_url}{page_num}"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            content = soup.find_all('div', class_='feed-item')

            # Iterate over each notice on the page
            for article in content:
                link = article.find('a', href=True)
                if link:
                    link = link['href']
                    full_link = 'https://www.thegazette.co.uk' + link
                    notice_data = scrape_notice(full_link, headers)
                    if notice_data:
                        data.append(notice_data)
                        print("Scraped:", notice_data)
                    else:
                        print("Error scraping notice:", full_link)
                time.sleep(1)  # Be polite and not bombard the server with requests

        else:
            print("Failed to retrieve page:", url)

    # Write data to CSV file
    with open('notices_data.csv', mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['Metadata Values', 'Notice Type', 'Notice Code', 'Notice Date', 'Notice ID',
                         'Deceased Surname', 'Deceased First Name', 'Address Line 1', 'Town', 'County',
                         'Additional Info'])
        writer.writerows(data)


if __name__ == "__main__":
    main()
