# OPEN WEATHER APP
This repository contains the project code for the **Open Weather App**. This application written in Python pulls the current weather forecast from selected cities from the Open Weather's API. 

The extracted data is stored into a DataFrame and then routed to a MongoDB instance for review. Finally an email notification containing an excel attachment along with an HTML report of the extracted weather data is sent to a recipient's email address using Mailguns API.  

**prerequisites**: You will need the following in order to use this project:

* Setup a user account with Open Weather to acquire API Key
* Setup an account with MongoDB to setup your own instance within free tier range
* Setup account with Mailgun to acquire your own API Key **Caution: There is a limit to how many emails you can send in free tier range**


**NOTE**: **This project uses an environment variable file ".env" to store credentials. You can switch this option to another preffered method if you like, just make sure to adjust the project code accordingly.**


## Part1: Reviewing Dockerfile
I've added a **Dockerfile** in case you would like to proceed with containerizing this application. Here are the docker commands you will need to use:  

```dockerfile
# Build the image 
docker build -t name_of_image .

# Run your app via container
docker run name_of_image

# If you would like to run the execution of your app within the container use:
docker start container_id_of_app
```

Your more then welcome to have this app run on a cron scheduler via a pipeline platform.  

Here's is the Dockerfile being used to run via docker container:

```Dockerfile
FROM python:3.10

WORKDIR /app 

COPY . .
RUN pip install -r requirements.txt

CMD ["python", "app.py"]
```

In short, we're using the Python 3.10 image and naming our work directory in the container called "/app". From there we copy the entire contents of our repo code into the work directory called "/app". From there we install the app package dependencies and then run the app via: `CMD ["python", "app.py"]`


## Part2: Open Weather Data Extraction
In this section we'll provide an overview of how the open weather data extraction works.  

Here is our starting point:

```py
def execute(self):
        geo_info_results = list(map(lambda zip_code: self.acquire_geo_location(zip_code), self.zip_codes))

        if geo_info_results is not None:
            geo_info_df = pd.DataFrame(geo_info_results)

            openwx_data_dict = {}
            openwx_data_dict.update(geo_info_df.apply(lambda row: self.acquire_region_weather(row['lat'], row['lon']), axis=1))

            openwx_data_list = [json.loads(value) for value in openwx_data_dict.values()]
            
            df = pd.DataFrame(openwx_data_list)
            flatten_df = json_normalize(df[0])
            cities = flatten_df['name'].to_list()
            flatten_df.to_excel(self.excel_file, index=False, header=True)

            try:
                sending_data_mongodb(flatten_df)

                html_table_blue_light = build_table(flatten_df, 'blue_light')
                with open(self.pretty_table, 'w') as f: f.write(html_table_blue_light)
                time.sleep(1)

                email_template_loc = self.emplate_template
                rendered_content = self.render_template(email_template_loc, zip_codes=self.zip_codes, cities=cities)
                self.render_template

                with open(self.rendered_report, 'w') as file: file.write(rendered_content)
                time.sleep(1)

                send_simple_message(self.recipent_address, self.email_subject, 
                                    self.email_body, self.rendered_report, self.excel_file)

            except Exception as e:
                print(e)
        else:
            print("Unable to fetch geo location data.")

```

In order for us to acquire the weather forecast data we need to acquire both the longitude and latitude of a given city/location. To get that info we pass the city's zip code to a function called **"acquire_geo_location"**.  

This line: `geo_info_results = list(map(lambda zip_code: self.acquire_geo_location(zip_code), self.zip_codes))`  

Takes a list of zip codes and calls the acquire_geo_location to acquire the longitude and latitude of each city. The return data is stored in a list.  

From there we check to make sure the list is not empty and proceed to create a dataframe from the previous list.  
Afterwards we run another execution passing the lat and lon of each city to a function called **acquire_region_weather**.  
The return data will proceed to be stored in a dictionary called **"openwx_data_dict"**. The data being return back is in json. We proceed to acquire the dictionary values by looping and storing the values in a list called **"openwx_data_list"**.  

Afterwards we create a pandas dataframe from the list data and proceed to use **json_normalize** to flatten the data making it more presentable in our reports. (Excel file and HTML table using the pretty_html_table module)

## Part3: Routing data to MongoDB
Below is the function used from our **database.py** file:

```py
def sending_data_mongodb(df):

    mdb_uname = os.getenv("MDB_UNAME")
    mdb_passwd = os.getenv("MDB_PASSWD")
    mdb_hostname = os.getenv("MDB_HOSTNAME")
    mdb_table = os.getenv("MDB_TABLE")
    mdb_collect_name = os.getenv("MDB_COLLECT_NAME")

    mongo_conn = f"mongodb+srv://{mdb_uname}:{mdb_passwd}@{mdb_hostname}/{mdb_table}"
    client = MongoClient(mongo_conn)
    db = client[os.getenv('MDB_TABLE')]
    records = df.to_dict(orient='records')
    collection = db[os.getenv('MDB_COLLECT_NAME')]

    try:
        collection.insert_many(records)
        print("SUCCESSFULL INSERTED RECORDS VIA MONGODB!!!\n")
    except Exception as e:
        print(e)

```

In short, we establish the mongo_db client connection and proceed to take the dataframe that is passed to our **sending_data_mongodb** function and send it to the targeted database/tablename in MongoDB. We use the "insert_many" method to apply a bulk insertion, then we print an alert letting us know the operation was successful. 


## Part4: Sending email notification using Mailgun's API

Below is the function used in our **mailgun_email.py** file:

```py
def send_simple_message(to, subject, body, html_file, excel_file):
        
        mg_api_key = os.getenv("MAILGUN_API_KEY")
        mg_domain = os.getenv("MAILGUN_DOMAIN")
        mg_url = os.getenv("MAILGUN_URL")

        html_report = open(html_file, 'rb')
        file_attachment = open(excel_file, 'rb')
    
        try: 
            print("Sending Email Notification...")
            return requests.post(
            f"{mg_url}{mg_domain}/messages", 
            auth=("api", mg_api_key), 
            files=[("attachment", file_attachment)],
            data={"from": f"Python Language Assistant <mailgun@{mg_domain}>", 
            "to": [to], 
            "subject": subject, 
            "text": body,
            "html": html_report})
        except Exception as e:
              print(e)
              print("Failed to send email!")

```

The function **send_simple_message** takes in several parameters and and sends an HTTP Post request using your mailgun domain and api key. The excel file will be the attachment added to the email and the html report will be body displayed in the email should your recipient allow html to be shown in emails. If it is turned off then the body variable value provided in the environment file will show for all plain-texted based emails. 