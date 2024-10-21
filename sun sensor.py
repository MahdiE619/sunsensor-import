import scrapy
import json
import requests
from tika import parser  

class SunSensorSpider(scrapy.Spider):
    name = 'sun_sensor_spider'
    start_urls = [
        'https://satsearch.co/products/categories/satellite/attitude/sensors/sun-sensor?page=1',
        'https://satsearch.co/products/categories/satellite/attitude/sensors/sun-sensor?page=2'
    ]

    def parse(self, response):
        products = []

        # استخراج نام و لینک محصولات از صفحه فعلی
        product_elements = response.css('div.card-text a')
        for product_element in product_elements:
            product_name = product_element.css('::text').get()
            product_url = product_element.css('::attr(href)').get()

            # افزودن محصول به لیست محصولات
            products.append({
                'name': product_name,
                'url': response.urljoin(product_url)
            })
            
            # ارسال درخواست به صفحه جزئیات محصول برای اطلاعات بیشتر
            yield scrapy.Request(
                response.urljoin(product_url),
                callback=self.parse_product_details,
                meta={'product_name': product_name, 'product_url': product_url}
            )

        # نمایش لیست محصولات برای تست
        print(json.dumps({'products': products}, indent=4))

    def parse_product_details(self, response):
        pname = response.meta.get('product_name')
        purl = response.meta.get('product_url')
        datasheet_link = response.css('.download-link.datasheet::attr(href)').get()
        product_details = {}

        # استخراج جزئیات محصول از صفحه جزئیات محصول
        detail_elements = response.css('div.col-6.col-md-5.py-3.px-4.border-bottom::text')
        for idx, detail_element in enumerate(detail_elements):
            detail_name = detail_element.get().strip()
            if detail_name:
                value_element = response.css('div.spec-value.border-bottom')[idx]
                detail_value = value_element.css('::text').get().strip()
                product_details[detail_name] = detail_value

        if not product_details and datasheet_link:
            # دانلود دیتاشیت
            datasheet_content = self.download_datasheet(datasheet_link)
            cleaned_datasheet_content = datasheet_content.replace('\n','')
            product_details['datasheet_content'] = cleaned_datasheet_content

        # ذخیره جزئیات محصول در یک فایل
        result = {
            'product_name': pname,
            'product_url': 'https://satsearch.co' + purl,
            'product_details': product_details
        }

        with open('sun_sensor_products.txt', 'a') as file:
            json.dump(result, file, indent=4)
            file.write('\n')  # افزودن یک خط جدید برای خوانایی بیشتر

    def download_datasheet(self, datasheet_link):
        # دانلود دیتاشیت
        response = requests.get(datasheet_link)

        # بررسی موفقیت‌آمیز بودن درخواست
        if response.status_code == 200:
            # ذخیره محتویات دیتاشیت به یک فایل موقت
            with open('datasheet_temp.pdf', 'wb') as temp_file:
                temp_file.write(response.content)
            raw = parser.from_file('datasheet_temp.pdf')

            # پاکسازی: حذف فایل موقت
            import os
            os.remove('datasheet_temp.pdf')

            return raw['content']

        else:
            print(f"Failed to download datasheet from {datasheet_link}")
            return None

# اجرای خزنده
if __name__ == '__main__':
    from scrapy.crawler import CrawlerProcess
    process = CrawlerProcess({
        'USER_AGENT': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)'
    })
    output = process.crawl(SunSensorSpider)
    process.start()
    print("output...")
    print(output)
    # for item in output:
    #     print(item)
