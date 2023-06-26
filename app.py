import streamlit as st
import requests


@st.cache_data(ttl=10, show_spinner=True)
def get_services(service_url):
    return requests.get(service_url, verify=False)


def delete_service(service_url, api_key):
    return requests.delete(service_url, json={'API-KEY': api_key}, verify=False)


def update_service(service_url, payload):
    return requests.post(service_url, json=payload, verify=False)


st.set_page_config(
    page_title="Microservice Updater",
    layout="wide"
)

st.title("Microservice Updater")

st.markdown("""
       This app fetches the latest version of deployed web services from the given endpoint of a *Microservice Updater*
       instance.
""")

url = st.text_input('URL of *Microservice Updater* instance', help="Enter the URL of the *Microservice Updater* you "
                                                                   "want to fetch the service list from.",
                    value="https://demos.swe.htwk-leipzig.de:40195")

api_key_field = st.text_input('API-KEY of *Microservice Updater* instance', type='password',
                              help='Enter the API-KEY necessary to access the service endpoints')

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

st.subheader('Register a new service')
mode = st.selectbox('Mode', ['docker', 'docker-compose', 'dockerfile'])
ports = st.text_input('Port mappings, *comma-separated list*')
volumes = st.text_input('Volume mappings, *comma-separated list*')

if mode == 'dockerfile':
    docker_image = st.text_input('Docker Image Name')
    docker_tag = st.text_input('Docker Image Tag')
    clone_url = None
else:
    docker_image = None
    docker_tag = None
    clone_url = st.text_input('Git Clone URL')

if st.button('Register new service'):
    if not api_key_field:
        st.error('API-KEY missing!')
    else:
        response = update_service(f'{url}/service',
                                  {'mode': mode, 'image': docker_image, 'tag': docker_tag, 'url': clone_url,
                                   'API-KEY': api_key_field, 'port': ports, 'volumes': volumes.split(',')})

        if response.ok:
            st.success(response.text)
        else:
            st.error(response.text)

if url:
    st.markdown(f"Fetching services from `{url}`...")

    # Fetch the services from the given URL using GET
    response = get_services(f'{url}/service')
    if response.status_code == 200:
        data = response.json()
        st.subheader(f"Found {len(data)} services")

        for service in data:
            placeholder = st.empty()

            with st.container():
                service_response = get_services(f'{url}/service/{service}')
                if service_response.status_code == 200:
                    service_data = service_response.json()
                else:
                    service_data = {}

                state = str(service_data["state"])

                headline_part, status_part, details_activator_part = st.columns([70, 20, 1])

                with headline_part:
                    if state == "RUNNING":
                        message = f" <span class='icon_ok'></span>"
                    else:
                        message = f" <span class='icon_warn'></span>"

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

                        if st.button('Delete'):
                            if not api_key_field:
                                st.error('API-KEY missing!')
                            else:
                                resp = delete_service(f'{url}/service/{service}', api_key_field)

                                if resp.ok:
                                    st.success(f'Service `{service}` removed')
                                else:
                                    st.error(f'Deletion failed: `{resp.text}`')
                        if st.button('Update'):
                            if not api_key_field:
                                st.error('API-KEY missing!')
                            else:
                                resp = update_service(f'{url}/service/{service}', {
                                    'API-KEY': api_key_field, 'volumes': container_volumes.split(',')})
                                if resp.ok:
                                    st.success(resp.text)
                                else:
                                    st.error(resp.text)
                    st.write("---")
    else:
        st.error(f"Error: `{response.status_code}`")
        st.stop()
