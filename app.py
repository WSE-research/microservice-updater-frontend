import streamlit as st
import requests

st.set_page_config(
    page_title="Microservice Updater",
    layout="wide"
)

st.title("Microservice Updater")

st.markdown("""
       This app fetches the latest version of deployed web services from the given endpoint of a *Microservice Updater* instance.
""")

url = st.text_input('URL of *Microservice Updater* instance', help="Enter the URL of the *Microservice Updater* you want to fetch the service list from.", value="https://demos.swe.htwk-leipzig.de:40195/service")

st.markdown("""
<style>
.warn {
    background-color: yellow;
    color: red;
}

.ok {
    background-color: lightgray;
    color: green;
}

.icon_warn::before {
    content: "⚠️";
    color: red;    
    background-color: yellow;
}

.icon_ok::before {
    content: "✅";
    color: green;
}    

.icon_warn::after, .icon_ok::after {
    content: " ";
}
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=60, show_spinner=True)
def get_services(url):
    return requests.get(url, verify=False)

if url:
    st.markdown(f"Fetching services from `{url}`...")
    
    # Fetch the services from the given URL using GET
    response = get_services(url)
    if response.status_code == 200:
        data = response.json()
        st.subheader(f"Found {len(data)} services")
        
        data.sort()
        
        for service in data:
            placeholder = st.empty()
            
            with st.container():
            
                service_response = get_services(url + "/" + service)
                if service_response.status_code == 200:
                    service_data = service_response.json()
                else:
                    service_data = {}
                    
                state = str(service_data["state"])
                if service_response.status_code == 200:
                    service_data = service_response.json()
                else:
                    service_data = {}

                headline_part, status_part, details_activator_part = st.columns([70,20,1])
                
                with headline_part: 
                    #errors = service_data["errors"]
                    #if errors:
                    #    message = f"*{errors}*"
                    #else:
                    #    message = ""
                    if state == "RUNNING":
                        message = f" <span class='icon_ok'></span>"
                    else:
                        message = f" <span class='icon_warn'></span>"
                        
                    st.markdown(message + "**" + service + "** ", unsafe_allow_html=True)

                with details_activator_part:
                    details = st.checkbox("Details", key=service, label_visibility="collapsed", help="Show details of the service.")
                
                with status_part:
                    if state == "RUNNING":
                        message = f" <span class='ok'>{state}</span>"
                    else:
                        message = f" <span class='warn'>{state}</span>"
                    
                    st.markdown(message, unsafe_allow_html=True)
                    
                values_part, actions_part = st.columns([2,1])                
                if details:
                    with values_part:
                        if service_response.status_code == 200:
                            #st.json(service_data)
                            properties = ""
                            for key in service_data:
                                if key == "id":
                                    continue
                                if key == "errors" and service_data[key]:
                                    st.warning(f"Error: `{service_data[key]}`")
                                    continue
                                if key == "state":
                                    state = service_data[key]
                                    if state == "RUNNING":
                                        st.success(f"State: `{state}`")
                                    else:
                                        st.error(f"State: `{state}`")
                                    continue
                                properties += f"* {key}: {service_data[key]}\n"
                            st.markdown(properties)
                        else:
                            st.error(f"Error: `{service_response.status_code}`")
                        
                    with actions_part:
                        st.markdown(f"Actions for `{service}`: <ul><li>TODO: Start</li><li>TODO: Stop</li><li>TODO: Restart</li></ul>", unsafe_allow_html=True)
                        
                    st.write("---")
    else:
        st.error(f"Error: `{response.status_code}`")
        st.stop()