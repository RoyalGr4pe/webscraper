### **Input data**

- urls: list[str]
    - A list of urls for any website, in any order
- batch_size: int
    - The number of urls scraped at a time
- scraping_data_file: filename
    - The individual scraping data for each website

```
"""

:data: This is the scraping data for a certain part of the website.

:multiple: Scrape for all the items with these properties. The max property is added to the last item to be scraped to specify the number of items to be found. The default is 8.

:attr: This is the attribute taken from the html for example the .text, href, src, srcset, etc.

:tag: The value of this is the tag name

:attr_name, attr_value: These are the attributes to look for in a tag for example class="some-class" or data-test="testing-data" etc. The attr_name is the first bit like class or data-test and the attr_value is what it is equal to

"""

"website1": {
    "root": "https://www.example.com",
    "type": "html",
    "data": { 
        "multiple root-item": {
            "item-data": [
                {
                    "tag": "tag_name",
                    "attr_name": "attr_value"
                },
                {
                    "tag": "tag_name",
                    "attr_name": "attr_value",
                    "max": 8
                }
            ],
            "sub-item1": {
                "item-data": [
                    {
                        "tag": "tag_name",
                        "attr_name": "attr_value",
                        "attr": ".text"
                    }
                ]
            },
            "sub-item2": {
                "item-data": [
                    {
                        "tag": "tag_name",
                        "attr_name": "attr_value",
                        "attr": "href"
                    }
                ]
            },
            ...
        }
    }
}
```


### **Output data**

- dict[dict] {"website1": [{"root-item": [{"sub-item1": "sub-item1-value"}, {"sub-item2": "sub-item2-value"}...]}]}