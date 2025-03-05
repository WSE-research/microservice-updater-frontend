import streamlit as st
from streamlit_javascript import st_javascript
import validators
import requests
import os
import json
from streamlit_extras.stylable_container import stylable_container
from streamlit_extras.add_vertical_space import add_vertical_space
from streamlit_extras.app_logo import add_logo


BACKEND_FALLBACK_URL = "https://localhost:5000"
api_key_error_message_text = 'API key is missing!'

@st.cache_data(ttl=10, show_spinner=True)
def get_services(service_url):
    return requests.get(service_url, verify=False)


def delete_service(service_url, api_key):
    return requests.delete(service_url, json={'API-KEY': api_key}, verify=False)


def update_service(service_url, payload):
    return requests.post(service_url, json=payload, verify=False)


def patch_service(service_url, payload):
    return requests.patch(service_url, json=payload, verify=False)

def hex2ascii(hex_string):
    byte_string = bytes.fromhex(hex_string)  
    ascii_string = byte_string.decode("ASCII")  
    return ascii_string

def register_new_service(endpoint, mode, docker_image, docker_tag, clone_url, api_key_field, ports, volumes):
    if not api_key_field:
        st.error(api_key_error_message_text)
        return
    
    response = update_service(endpoint,
                            {'mode': mode, 
                             'image': docker_image, 
                             'tag': docker_tag, 
                             'url': clone_url,
                             'API-KEY': api_key_field, 
                             'port': ports, 
                             'volumes': volumes.split(',')})
    if response.ok:
        json_response = response.json()
        st.success(f"Service {json_response.get('id')} registered successfully ({json_response.get('state')}, {response.text})")
        st.balloons()
    else:
        st.error(response.text)

st.set_page_config(
    page_title="Microservice Updater",
    layout="wide"
)


title_container = st.container()
col1, col2 = st.columns([1, 50], vertical_alignment="bottom", gap="small")
with title_container:
    with col1:
        st.image("images/logo.png", width=48)
    with col2:
        st.title("Microservice Updater")
st.markdown("""This app fetches the latest version of deployed web services from the given endpoint of a *Microservice Updater* instance.""")
add_logo("images/logo.png", height=300)


# if questionmark is present, then search for the app_url
if "?" in st.query_params:
    app_url = st.query_params["?"].split("?")[0]
else:
    app_url = st_javascript("await fetch('').then(r => window.parent.location.href)").split("?")[0]

backend_url = st.query_params["backend_url"] if "backend_url" in st.query_params else os.getenv('BACKEND_URL', BACKEND_FALLBACK_URL)
if not validators.url(backend_url):
    st.warning(f"Invalid backend URL: `{backend_url}`. Falling back to default URL: `{BACKEND_FALLBACK_URL}`")  
if backend_url.endswith('service/') or backend_url.endswith('service'):
    st.warning("Backend URL should not end with `service` or `service/`. Please remove it from the URL.")


url = st.text_input(
    'URL of *Microservice Updater* instance', 
    help="Enter the URL of the *Microservice Updater* you want to fetch the service list from.",
    value=backend_url,
    key="backend_url"
)

api_key_field = st.text_input(
    'API key of *Microservice Updater* instance', 
    type='password',
    help='Enter the API key necessary to access the service endpoints',
    value=hex2ascii(st.query_params["api_key"]) if "api_key" in st.query_params else "",
    key="api_key"
)

if api_key_field:
    bookmark_url =  app_url + "?api_key=" + api_key_field.encode('utf-8').hex() + "&backend_url=" + url
    with st.expander("For your bookmarks: See the URL to the current service configuration for easier access.", expanded=False):
        st.code(bookmark_url)

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

endpoint = url + '/service'

# block for creating a new service
with stylable_container(
        key="container_with_border",
        css_styles="""
            {
                border: 2px solid rgba(49, 51, 63, 0.2);
                border-radius: 0.5rem;
                padding: calc(1em - 1px);
                border-color: #FF3399;
            }
            """,
    ):
    with st.expander("🆕 Create a new service", expanded=False):
        st.subheader('Register a new service')
        st.markdown("""
            You can register a new service by providing the requested information here.
            There are 3 modes available (docker, docker-compose, dockerfile) to initialize the automatic rollout of your service. 
            Please see the [documentation](https://github.com/WSE-research/microservice-updater/blob/master/README.md#api-endpoints) for details.
        """)

        mode = st.selectbox('Mode', ['json', 'dockerfile', 'docker', 'docker-compose'])
        ports = None
        
        if mode == 'json':
            config_text = ""
            json_config = st.text_area(label="Enter the JSON configuration for the service (service_config.json):", height=250, key="json_config")
            if json_config != "":
                try:    
                    json_config = json.loads(json_config)
                    if json_config.get('services', None) is not None:
                        json_config = json_config.get('services')[0]

                    docker_image = json_config.get('image', None)
                    docker_tag = json_config.get('tag', None)
                    ports = json_config.get('port', None)
                    volumes = json_config.get('volumes', None)
                    mode = json_config.get('mode', None)
                    clone_url = json_config.get('url', None)
                    
                    if volumes is None:
                        volumes = ""

                    # create a dict from the values 
                    config_dict = {
                        'mode': mode,
                        'docker_image': docker_image,
                        'docker_tag': docker_tag,
                        'ports': ports,
                        'volumes': volumes,
                        'clone_url': clone_url
                    }
                    for key, value in config_dict.items():
                        config_left1, config_right1 = st.columns([1, 4], vertical_alignment="center")
                        with config_left1:
                            st.write(f'{key}:')
                        with config_right1:
                            st.code(value)
                        
                except json.JSONDecodeError:
                    st.error('Invalid JSON configuration')
                
            else:
                st.warning('No JSON configuration provided')
            
        else:
            ports = st.text_input('Port mappings, *comma-separated list*', help='e.g., `8080:80,5000:3030`')
            volumes = st.text_input('Volume mappings, *comma-separated list*')
            
            if mode == 'dockerfile':
                docker_image = st.text_input('Docker Image Name', help='without Docker image tag')
                docker_tag = st.text_input('Docker Image Tag', help='e.g., `latest`')
                clone_url = None
            else:
                docker_image = None
                docker_tag = None
                clone_url = st.text_input('Git Clone URL')

        if ports != None and ports != "":
            with stylable_container(
                "green",
                css_styles="""
                button {
                    background-color: #66FF66;
                    border-color: #009900;
                    color: black;
                }"""
            ):
                if st.button('🆕 Register new service', key="button1"):
                    with st.spinner("waiting for response of creater ...", show_time=True):
                        result = register_new_service(endpoint, mode, docker_image, docker_tag, clone_url, 
                                    api_key_field, ports, volumes)
                        if result:
                            st.success(f"Service {result.get('id')} registered successfully ({result.get('state')})")
                        else:
                            st.error("Service registration failed")

            with stylable_container(
                "cyan",
                css_styles="""
                button {
                    background-color: #66FFFF;
                    border-color: #009999;
                    color: black;
                }""",
            ):
                if st.button('🗑️+🆕 Delete and thereafter register as a new service', key="button2"):
                    service = docker_image.replace('/', '-')
                    st.info(f"Deleting service `{service}` and registering as new service")
                    if not api_key_field:
                        st.error(api_key_error_message_text)
                    else:
                        with st.spinner("waiting for response of deleter ...", show_time=True):
                            resp = delete_service(f'{endpoint}/{service}', api_key_field)

                        if resp.ok:
                            st.success(f'Service `{service}` removed')

                            with st.spinner("waiting for response of creater ...", show_time=True):
                                register_new_service(endpoint, mode, docker_image, docker_tag, clone_url, 
                                        api_key_field, ports, volumes)
                        else:
                            st.error(f'Deletion failed: `{resp.text}`')


# add vertical space between the create service and the filter services sections
add_vertical_space(3)

filter_string = st.text_input('Filter services by name (string)', key="filter", help="full-text match on service name").lower()

if url:
    st.markdown(f"Fetching services from `{endpoint}`...")

    # Fetch the services from the given URL using GET
    try:
        response = get_services(f'{endpoint}')
    except requests.exceptions.ConnectionError:
        st.error(f"""
            Connection error while trying to fetch services from the given URL: {endpoint}. 
            *Microservice Updater* web service address was set to {url}. 
            Please check the above URL field or set the `BACKEND_URL` environment variable (`export BACKEND_URL=...`). 
        """)
        st.stop()

    if response.status_code == 200:
        data = response.json()            
        additional_filter_info = ""
        if filter_string:
            additional_filter_info = f" (filtered by `{filter_string}`)"
        st.subheader(f"Found {len(data)} services {additional_filter_info}")
        st.markdown("""The list will not refresh automatically. Click the checkbox to see details and actions for each service.""")

        for service in data:
            if filter_string and filter_string not in service:
                continue
            
            placeholder = st.empty()
            
            try:
                with st.container():
                    service_response = get_services(f'{endpoint}/{service}')
                    if service_response.status_code == 200:
                        service_data = service_response.json()
                    else:
                        service_data = {}

                    if "state" in service_data:
                        state = str(service_data["state"])
                    else:
                        st.error(f"Error: `{service_response.status_code}` for service `{service}`: `{service_response.text}`")
                        state = "UNKNOWN"

                    headline_part, status_part, details_activator_part = st.columns([70, 20, 1])

                    with headline_part:
                        if state == "RUNNING":
                            message = " <span class='icon_ok'></span>"
                        else:
                            service_data = {}

                        headline_part, status_part, details_activator_part = st.columns([70, 20, 1])

                        with headline_part:
                            if state == "RUNNING":
                                message = " <span class='icon_ok'></span>"
                            else:
                                message = " <span class='icon_warn'></span>"

                            st.markdown(message + "**" + service + "** ", unsafe_allow_html=True)

                        with details_activator_part:
                            details = st.checkbox("Details", key=service, label_visibility="collapsed",
                                                help="Show details of the service.")

                        with status_part:
                            if state == "RUNNING":
                                message = f" <span class='ok'>{state}</span>"
                            else:
                                message = f" <span class='warn'>{state}</span>"

                            st.markdown(message, unsafe_allow_html=True)

                        values_part, actions_part = st.columns([2, 1])
                        if details:
                            with values_part:
                                if service_response.status_code == 200:
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
                                st.markdown(f"Actions for `{service}`", unsafe_allow_html=True)

                                container_volumes = st.text_input('Volume mappings, *required for updates*')
                                container_tag = st.text_input('Docker image tag')
                                container_ports = st.text_input('Port mappings')

                                if st.button('Delete'):
                                    if not api_key_field:
                                        st.error(api_key_error_message_text)
                                    else:
                                        resp = delete_service(f'{endpoint}/{service}', api_key_field)

                                        if resp.ok:
                                            st.success(f'Service `{service}` removed')
                                        else:
                                            st.error(f'Deletion failed: `{resp.text}`')
                                if st.button('Update'):
                                    if not api_key_field:
                                        st.error(api_key_error_message_text)
                                    else:
                                        resp = update_service(f'{endpoint}/{service}', {
                                            'API-KEY': api_key_field, 'volumes': container_volumes.split(',')})
                                        if resp.ok:
                                            st.success(resp.text)
                                        else:
                                            st.error(resp.text)
                                if st.button('Edit settings'):
                                    if not api_key_field:
                                        st.error(api_key_error_message_text)
                                    else:
                                        resp = patch_service(f'{endpoint}/{service}', {
                                            'tag': container_tag, 'port': container_ports, 'API-KEY': api_key_field,
                                            'volumes': container_volumes.split(',')})
                                        if resp.ok:
                                            st.success(resp.text)
                                        else:
                                            st.error(resp.text)
                            st.write("---")
            except Exception as e:
                st.error(f"Error for {service}: `{e}`")
                continue
    else:
        st.error(f"Error: `{response.status_code}`")
        st.stop()


