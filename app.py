
import streamlit as st
from datetime import date, timedelta, datetime
import random
import time
import io
import streamlit.components.v1 as components
from PIL import Image, ImageDraw

# --- 1. OPTIMIZED SETUPS & LIGHTWEIGHT CSS ---
st.set_page_config(page_title="HimYatra Bus", layout="centered")

st.markdown("""
<style>
    @keyframes fadeIn {
        0% { opacity: 0; transform: translateY(8px); }
        100% { opacity: 1; transform: translateY(0); }
    }
    .animate-box { animation: fadeIn 0.3s ease-out forwards; }
    .stButton>button { transition: transform 0.1s; border-radius: 8px; font-weight: bold; }
    .stButton>button:active { transform: scale(0.96); }

    div[data-testid="stDialog"] div[role="dialog"] {
        border-radius: 16px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    }
</style>
""", unsafe_allow_html=True)

# --- 2. KNOWN COORDINATES FOR REGIONAL STOPS ---
LOCATION_COORDS = {
    "GGI Khanna": [30.7073, 76.2163],
    "Ropar": [30.9664, 76.5331],
    "Kiratpur": [31.1812, 76.5684],
    "Anandpur Sahib": [31.2356, 76.4988],
    "Nawanshahr": [31.1256, 76.1186],
    "Swarghat": [31.2294, 76.7118],
    "Dadhol": [31.4245, 76.7020],
    "Ukli": [31.4680, 76.6800],
    "Dangar 174023": [31.4503, 76.6698],
    "Mair": [31.4880, 76.6450],
    "Bhota": [31.5412, 76.6214],
    "Ghumarwin": [31.4428, 76.7145],
    "Bilaspur": [31.3417, 76.7611]
}

# --- 3. BUS DATABASE ---
BUSES = [
    {
        "id": "B1",
        "name": "Bilaspur Royal",
        "route": "Khanna -> Ropar -> Kiratpur -> Swarghat -> Dadhol -> Dangar -> Ghumarwin -> Bilaspur",
        "type": "Non-AC Semi-Deluxe",
        "fare": 320,
        "local_stops": True,
        "stops": ["GGI Khanna", "Ropar", "Kiratpur", "Swarghat", "Dadhol", "Dangar 174023", "Ghumarwin", "Bilaspur"]
    },
    {
        "id": "B2",
        "name": "HRTC Ordinary",
        "route": "Khanna -> Nawanshahr -> Anandpur Sahib -> Mair -> Bhota -> Ukli -> Dadhol -> Dangar",
        "type": "Local Ordinary",
        "fare": 210,
        "local_stops": True,
        "stops": ["GGI Khanna", "Nawanshahr", "Anandpur Sahib", "Mair", "Bhota", "Ukli", "Dadhol", "Dangar 174023"]
    },
    {
        "id": "B3",
        "name": "Northern Volvo",
        "route": "Chandigarh -> Ropar Toll -> Bilaspur Bus Stand",
        "type": "AC Volvo",
        "fare": 580,
        "local_stops": False,
        "stops": ["Ropar", "Bilaspur"]
    },
    {
        "id": "B4",
        "name": "Shivalik Gramin Shuttle",
        "route": "Ropar -> Kiratpur -> Mair -> Ukli -> Ghumarwin",
        "type": "Local Rural",
        "fare": 240,
        "local_stops": True,
        "stops": ["Ropar", "Kiratpur", "Mair", "Ukli", "Ghumarwin"]
    }
]

def get_seats(bus_id, travel_date):
    random.seed(f"{bus_id}{travel_date}")
    return random.randint(2, 25)

# Session state initialization
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "my_tickets" not in st.session_state:
    st.session_state.my_tickets = []
if "route_preference" not in st.session_state:
    st.session_state.route_preference = "Local"
if "origin_loc" not in st.session_state:
    st.session_state.origin_loc = "GGI Khanna"
if "dest_loc" not in st.session_state:
    st.session_state.dest_loc = "Dangar 174023"
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = [
        {"role": "assistant", "content": "Hey bro! I can help you pick stops like Bhota, Mair, Dadhol, Ukli, or Dangar. Ask me anything!"}
    ]

# --- 4. LEAFLET INTERACTIVE ROUTE MAP ---
def render_route_map(start_name, end_name):
    start_coords = LOCATION_COORDS.get(start_name, [30.7073, 76.2163])
    end_coords = LOCATION_COORDS.get(end_name, [31.4503, 76.6698])
    center_lat = (start_coords[0] + end_coords[0]) / 2
    center_lon = (start_coords[1] + end_coords[1]) / 2

    map_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <style>
            #map {{ height: 320px; width: 100%; border-radius: 12px; }}
        </style>
    </head>
    <body>
        <div id="map"></div>
        <script>
            var map = L.map('map').setView([{center_lat}, {center_lon}], 8);
            L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                maxZoom: 18,
                attribution: '© OpenStreetMap contributors'
            }}).addTo(map);

            var startMarker = L.marker([{start_coords[0]}, {start_coords[1]}]).addTo(map)
                .bindPopup("🟢 <b>Pickup:</b> {start_name}").openPopup();

            var endMarker = L.marker([{end_coords[0]}, {end_coords[1]}]).addTo(map)
                .bindPopup("🔴 <b>Destination:</b> {end_name}");

            var latlngs = [
                [{start_coords[0]}, {start_coords[1]}],
                [{end_coords[0]}, {end_coords[1]}]
            ];
            var polyline = L.polyline(latlngs, {{color: '#0f62fe', weight: 4, dashArray: '6, 8'}}).addTo(map);
            map.fitBounds(polyline.getBounds(), {{padding: [40, 40]}});
        </script>
    </body>
    </html>
    """
    components.html(map_html, height=335)

# --- 5. CASUAL AI AGENT LOGIC ---
def analyze_query_with_ai(query):
    q = query.lower()
    
    matched = None
    for loc in LOCATION_COORDS.keys():
        if loc.lower().split()[0] in q:
            matched = loc
            break
            
    if matched:
        st.session_state.dest_loc = matched
        matching_buses = [b for b in BUSES if any(matched.lower().split()[0] in s.lower() for s in b["stops"])]
        
        bus_list = "\n".join([f"• **{b['name']}** (₹{b['fare']})" for b in matching_buses]) if matching_buses else "Local ordinary buses."
        return f"Got it bro! I updated your destination on the map to **{matched}**.\n\nBuses going there:\n{bus_list}"

    if any(w in q for w in ["cheap", "cheapest", "sasta", "low price", "fare"]):
        return "Bro, **HRTC Ordinary** is the cheapest at just **₹210**. Takes small rural bazaar stops all the way."

    if any(w in q for w in ["ac", "volvo", "fast"]):
        return "Take **Northern Volvo** (₹580) for AC comfort, but remember it drops only at main terminals, not small bazaars!"

    return "Tell me which stop you need (Bhota, Mair, Ukli, Dadhol, Dangar) and I'll plot it on the map and find the best bus!"

# --- 6. TICKET IMAGE GENERATOR ---
def create_ticket_image(ticket_data):
    width, height = 700, 420
    img = Image.new("RGB", (width, height), color="#ffffff")
    draw = ImageDraw.Draw(img)

    draw.rectangle([(0, 0), (width, 80)], fill="#0f62fe")
    draw.text((25, 25), "HIMYATRA EXPRESS - BOARDING PASS", fill="#ffffff")
    draw.line([(0, 80), (width, 80)], fill="#0043ce", width=2)
    
    details = [
        f"Ticket ID      : {ticket_data['id']}",
        f"Passenger Name : {ticket_data['name']}",
        f"Mobile Number  : +91 {ticket_data['phone']}",
        f"Bus Name       : {ticket_data['bus']}",
        f"Route          : {ticket_data['route']}",
        f"Travel Date    : {ticket_data['date']}",
        f"Seat Number    : {ticket_data['seat']}",
        f"Total Paid     : INR {ticket_data['fare']}.00 ({ticket_data['payment']})",
        f"Status         : CONFIRMED & VERIFIED"
    ]

    y_pos = 110
    for line in details:
        draw.text((35, y_pos), line, fill="#212529")
        y_pos += 28

    draw.rectangle([(10, 10), (width - 10, height - 10)], outline="#0f62fe", width=3)
    draw.rectangle([(510, 260), (660, 380)], outline="#24a148", width=2)
    draw.text((540, 310), "[ PAID ]", fill="#24a148")
    draw.text((525, 335), "OFFICIAL PASS", fill="#24a148")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

# --- 7. LOGIN GATEWAY ---
if not st.session_state.logged_in:
    st.markdown("<h2 class='animate-box'>🔒 Passenger Login</h2>", unsafe_allow_html=True)
    st.write("Please verify your phone number to proceed.")
    
    with st.container(border=True):
        phone = st.text_input("Enter 10-Digit Mobile Number", max_chars=10, placeholder="9876543210")
        
        if len(phone) == 10:
            st.success("Valid number format. OTP sent to your phone!")
            otp = st.text_input("Enter OTP (Hint: Type 1234)", max_chars=4)
            
            if otp == "1234":
                if st.button("Verify & Enter App", use_container_width=True, type="primary"):
                    st.session_state.logged_in = True
                    st.session_state.phone = phone
                    st.rerun() 
            elif len(otp) == 4:
                st.error("Incorrect OTP. Try 1234.")
    st.stop()

# --- 8. FLOATING AI CHAT POPUP ---
@st.dialog("💬 Travel Buddy Assistant")
def show_chat_popup():
    st.caption("Ask anything about Bhota, Mair, Dangar, bus fares, or travel rush.")
    chat_container = st.container(height=350)
    with chat_container:
        for msg in st.session_state.chat_messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                
    user_query = st.chat_input("Type your question here...")
    if user_query:
        st.session_state.chat_messages.append({"role": "user", "content": user_query})
        reply = analyze_query_with_ai(user_query)
        st.session_state.chat_messages.append({"role": "assistant", "content": reply})
        st.rerun()

# --- 9. MAIN DASHBOARD ---
st.markdown("<h2 class='animate-box'>🚌 HimYatra Dashboard</h2>", unsafe_allow_html=True)

top_col1, top_col2 = st.columns([3, 1])
with top_col1:
    st.caption(f"Verified Passenger: +91 {st.session_state.phone}")
with top_col2:
    if st.button("🤖 Ask AI", use_container_width=True, type="primary"):
        show_chat_popup()

tab_search, tab_tickets, tab_ai = st.tabs(["🎫 Book Bus", "🎟️ My Tickets", "📅 5-Day Rush Predictor"])

# ================= TAB 1: SEARCH & BOOK =================
with tab_search:
    st.markdown("<div class='animate-box'>", unsafe_allow_html=True)
    
    # Visual Interactive Selector
    st.subheader("📍 Select Your Route on Map")
    
    c1, c2 = st.columns(2)
    with c1:
        origin_choice = st.selectbox(
            "🟢 Pickup Point (Where you are)",
            list(LOCATION_COORDS.keys()),
            index=list(LOCATION_COORDS.keys()).index(st.session_state.origin_loc)
        )
        st.session_state.origin_loc = origin_choice
        
    with c2:
        dest_choice = st.selectbox(
            "🔴 Destination (Where you wanna go)",
            list(LOCATION_COORDS.keys()),
            index=list(LOCATION_COORDS.keys()).index(st.session_state.dest_loc) if st.session_state.dest_loc in LOCATION_COORDS else 8
        )
        st.session_state.dest_loc = dest_choice

    travel_date = st.date_input("Travel Date", min_value=date.today())

    # RENDER THE DYNAMIC MAP WITH SELECTED MARKERS
    render_route_map(st.session_state.origin_loc, st.session_state.dest_loc)

    st.write("---")
    st.subheader("📍 Route Type Preference")
    
    col1, col2 = st.columns(2)
    if col1.button("🏡 VILLAGE & LOCAL DROPS\n(Stops at Bhota, Mair, Dangar)", use_container_width=True):
        st.session_state.route_preference = "Local"
    if col2.button("🛣️ EXPRESS / HIGHWAY ONLY\n(Main Bus Stands Only)", use_container_width=True):
        st.session_state.route_preference = "Express"
        
    if st.session_state.route_preference == "Local":
        st.success(f"✅ Showing buses that drop right at **{st.session_state.dest_loc}**.")
    else:
        st.info("⚡ Showing express buses. (Bypasses small village stops)")
        
    st.write("---")
    
    # Filter buses
    for bus in BUSES:
        if st.session_state.route_preference == "Local" and not bus["local_stops"]:
            continue
            
        seats_left = get_seats(bus["id"], travel_date)
        
        with st.container(border=True):
            st.markdown(f"### {bus['name']} ({bus['type']})")
            st.write(f"📍 **Route:** {bus['route']}")
            st.write(f"💰 **Fare:** ₹{bus['fare']} | 🪑 **Seats Left:** {seats_left}")
            
            with st.expander("👉 Click here to Book & Pay"):
                passenger_name = st.text_input("Passenger Name", key=f"name_{bus['id']}")
                seat_choice = st.selectbox("Choose Seat", range(1, seats_left + 1), key=f"seat_{bus['id']}")
                
                st.write("**Select Payment Method:**")
                payment_method = st.radio(
                    "Payment Options", 
                    ["FamApp (UPI)", "Samsung Wallet", "PayPal", "Credit/Debit Card"], 
                    key=f"pay_{bus['id']}",
                    label_visibility="collapsed"
                )
                
                if st.button(f"Pay ₹{bus['fare']} & Confirm", type="primary", key=f"confirm_{bus['id']}"):
                    if passenger_name == "":
                        st.error("Please enter a name!")
                    else:
                        with st.spinner(f"Processing ₹{bus['fare']} via {payment_method}..."):
                            time.sleep(1.2)
                        
                        ticket_id = f"TKT-{random.randint(1000,9999)}"
                        current_time = datetime.now().strftime("%d-%m-%Y %I:%M %p")
                        
                        receipt_text = f"""==================================================
              HIMYATRA OFFICIAL RECEIPT
==================================================
Booking Reference : {ticket_id}
Issued On         : {current_time}

PASSENGER DETAILS:
• Name            : {passenger_name}
• Contact         : +91 {st.session_state.phone}

JOURNEY DETAILS:
• Service         : {bus['name']} ({bus['type']})
• Route           : {st.session_state.origin_loc} -> {st.session_state.dest_loc}
• Journey Date    : {travel_date}
• Allocated Seat  : Seat #{seat_choice}

PAYMENT SUMMARY:
• Fare Amount     : INR {bus['fare']}.00
• Payment Mode    : {payment_method}
• Payment Status  : SUCCESS / CONFIRMED
==================================================
Present this pass upon boarding the vehicle. Safe travels!"""

                        ticket_record = {
                            "id": ticket_id,
                            "bus": bus["name"],
                            "route": f"{st.session_state.origin_loc} -> {st.session_state.dest_loc}",
                            "date": str(travel_date),
                            "name": passenger_name,
                            "phone": st.session_state.phone,
                            "seat": seat_choice,
                            "fare": bus["fare"],
                            "payment": payment_method,
                            "receipt": receipt_text
                        }
                        
                        st.session_state.my_tickets.append(ticket_record)
                        st.success(f"Payment Confirmed! Ticket ID: {ticket_id}")
                        st.balloons()
                        
                        with st.container(border=True):
                            st.markdown("#### 📄 Booking Invoice")
                            st.write(f"**Ticket ID:** `{ticket_id}` | **Passenger:** {passenger_name}")
                            st.write(f"**Trip:** {st.session_state.origin_loc} ➔ {st.session_state.dest_loc}")
                            st.write(f"**Bus:** {bus['name']} | **Seat:** #{seat_choice} | **Date:** {travel_date}")
                            st.write(f"**Amount Paid:** ₹{bus['fare']} via {payment_method}")
                        
                        img_bytes = create_ticket_image(ticket_record)
                        
                        dl_col1, dl_col2 = st.columns(2)
                        with dl_col1:
                            st.download_button(
                                label="🖼️ Download Ticket (Image)",
                                data=img_bytes,
                                file_name=f"HimYatra_Pass_{ticket_id}.png",
                                mime="image/png",
                                key=f"dl_img_{ticket_id}"
                            )
                        with dl_col2:
                            st.download_button(
                                label="📝 Download Receipt (Notepad .txt)",
                                data=receipt_text,
                                file_name=f"HimYatra_Receipt_{ticket_id}.txt",
                                mime="text/plain",
                                key=f"dl_txt_{ticket_id}"
                            )
                        
    st.markdown("</div>", unsafe_allow_html=True)

# ================= TAB 2: MY TICKETS =================
with tab_tickets:
    st.markdown("<div class='animate-box'>", unsafe_allow_html=True)
    st.subheader("Your Confirmed Bookings & Receipts")
    
    if len(st.session_state.my_tickets) == 0:
        st.info("No tickets booked yet.")
    else:
        for tkt in reversed(st.session_state.my_tickets):
            with st.container(border=True):
                st.markdown(f"**Ticket ID:** `{tkt['id']}`")
                st.write(f"👤 **Passenger:** {tkt['name']} (+91 {tkt['phone']})")
                st.write(f"🚌 **Bus:** {tkt['bus']} | 🪑 **Seat:** #{tkt['seat']}")
                st.write(f"📍 **Route:** {tkt['route']}")
                st.write(f"📅 **Date:** {tkt['date']} | 💰 **Paid:** ₹{tkt['fare']} via {tkt['payment']}")
                
                hist_img_bytes = create_ticket_image(tkt)
                d_c1, d_c2 = st.columns(2)
                with d_c1:
                    st.download_button(
                        label="🖼️ Download Image Ticket",
                        data=hist_img_bytes,
                        file_name=f"HimYatra_Pass_{tkt['id']}.png",
                        mime="image/png",
                        key=f"hist_img_{tkt['id']}"
                    )
                with d_c2:
                    st.download_button(
                        label="📝 Download Notepad (.txt)",
                        data=tkt["receipt"],
                        file_name=f"HimYatra_Receipt_{tkt['id']}.txt",
                        mime="text/plain",
                        key=f"hist_txt_{tkt['id']}"
                    )
    st.markdown("</div>", unsafe_allow_html=True)

# ================= TAB 3: 5-DAY RUSH PREDICTOR =================
with tab_ai:
    st.markdown("<div class='animate-box'>", unsafe_allow_html=True)
    st.subheader("AI 5-Day Rush Predictor")
    st.write("Check ±2 days to find the best travel day.")
    
    target_bus = st.selectbox("Select Bus for Prediction", [b["name"] for b in BUSES])
    bus_id = next(b["id"] for b in BUSES if b["name"] == target_bus)
    
    for i in range(-2, 3):
        check_date = travel_date + timedelta(days=i)
        seats_left = get_seats(bus_id, check_date)
        
        if seats_left > 15:
            rush = "🟢 Low Rush"
        elif seats_left > 8:
            rush = "🟡 Medium Rush"
        else:
            rush = "🔴 High Rush"
            
        is_selected = "⭐ (Your Date)" if i == 0 else ""
        st.write(f"**{check_date.strftime('%d %b')}** {is_selected} : {seats_left} seats left — {rush}")
        
    st.markdown("</div>", unsafe_allow_html=True)