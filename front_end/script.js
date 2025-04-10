const API_BASE_URL = "https://127.0.0.1:8443/api"; // ✅ Use HTTPS

document.addEventListener("DOMContentLoaded", function () {
    let mainContent = document.getElementById("main-content");

    /** =================== Utility Functions =================== **/

    async function loadPage(url, callback) {
        try {
            console.log(`📌 Fetching ${url}...`);
            let response = await fetch(url);
            if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
    
            let data = await response.text();
            mainContent.innerHTML = data; // ✅ Ensure the content is replaced
            console.log("✅ Page loaded successfully:", url);
    
            if (callback) await callback(); // ✅ Ensure callback runs after the page loads
        } catch (error) {
            console.error("❌ Error loading page:", error);
        }
    }

    function setActiveMenu(activeLink) {
        document.querySelectorAll(".nav-link").forEach(link => link.classList.remove("active"));
        activeLink.classList.add("active");
    }

    /** =================== Navigation Events =================== **/

    document.getElementById("dashboard-link").addEventListener("click", function (event) {
        event.preventDefault();
        setActiveMenu(this);
        location.reload();
    });

    document.getElementById("config-link").addEventListener("click", function (event) {
        event.preventDefault();
        setActiveMenu(this);
        loadPage("configuration.html", () => console.log("Configuration page loaded."));
    });

    document.addEventListener("click", function (event) {
        if (event.target.id === "back-to-dashboard") {
            event.preventDefault();
            location.reload();
        }
    });

    /** =================== Dashboard Statistics =================== **/

    async function loadDashboardStats() {
        try {
            let response = await fetch(`${API_BASE_URL}/eids/`, {
                method: "GET",
                mode: "cors",
                cache: "no-store", // ✅ Prevent caching issues
                headers: { "Content-Type": "application/json" }
            });
    
            if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
    
            let eids = await response.json();
            console.log("✅ API Response:", eids); // ✅ Debug API response
    
            if (!Array.isArray(eids)) {
                console.error("❌ Unexpected response format:", eids);
                return;
            }
    
            let totalEIDs = eids.length;
            let totalProfilesInstalled = 0;
            let totalActiveProfiles = 0;
    
            eids.forEach(eid => {
                totalProfilesInstalled += eid.activation_codes.filter(code => code.state === "complete").length;
                if (eid.active_profile) totalActiveProfiles += 1;
            });
    
            // ✅ Ensure elements exist before updating them
            let totalEsimElement = document.getElementById("total-esim");
            if (totalEsimElement) totalEsimElement.innerText = totalEIDs;
    
            let profileInstalledElement = document.getElementById("profile-installed");
            if (profileInstalledElement) profileInstalledElement.innerText = totalProfilesInstalled;
    
            let activeProfileElement = document.getElementById("active-profile");
            if (activeProfileElement) activeProfileElement.innerText = totalActiveProfiles;
    
        } catch (error) {
            console.error("❌ Error loading dashboard statistics:", error);
        }
    }
    
    loadDashboardStats();

    /** =================== Add EID Functionality =================== **/

    document.addEventListener("click", function (event) {
        if (event.target.id === "add-eid-btn") {
            let addEidModal = new bootstrap.Modal(document.getElementById("addEidModal"));
            addEidModal.show();
        }
    });

    document.addEventListener("click", function (event) {
        if (event.target.id === "saveEidBtn") {
            addNewEID();
        }
    });

    async function addNewEID() {
        let eidName = document.getElementById("eidName").value.trim();
        let eidDescription = document.getElementById("eidDescription").value.trim();
        let numProfiles = parseInt(document.getElementById("numOfProfile").value);
        let activeProfile = document.getElementById("activeProfile").value.trim();
    
        if (!eidName || !eidDescription || isNaN(numProfiles)) {
            alert("Please fill in all fields.");
            return;
        }
    
        let eidData = {
            eid_name: eidName,
            description: eidDescription,
            num_profiles: numProfiles,
            active_profile: activeProfile,
            activation_codes: []
        };
    
        try {
            let response = await fetch(`${API_BASE_URL}/add-eid/`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(eidData),
                cache: "no-store"
            });
    
            if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
    
            let newEid = await response.json();
            console.log("✅ New EID added:", newEid);
    
            alert("EID successfully added!");
    
            // ✅ Hide modal, reset form, and reload data
            bootstrap.Modal.getInstance(document.getElementById("addEidModal")).hide();
            document.getElementById("addEidForm").reset();
            
            await loadEidList(); // ✅ Ensure the new EID appears
            await loadDashboardStats(); // ✅ Update dashboard
    
        } catch (error) {
            console.error("❌ Error adding EID:", error);
            alert("Failed to add EID. Please try again.");
        }
    }
    

    /** =================== Fetch and Display EIDs =================== **/

    async function loadEidList() {
        try {
            let response = await fetch(`${API_BASE_URL}/eids/`, {
                method: "GET",
                mode: "cors",
                cache: "no-store",
                headers: { "Content-Type": "application/json" }
            });
    
            if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
    
            let eids = await response.json();
            console.log("✅ EID List:", eids);
    
            let tableBody = document.getElementById("esim-table");
            if (!tableBody) {
                console.error("❌ Table body element not found!");
                return;
            }
    
            tableBody.innerHTML = ""; // ✅ Clear previous content
    
            eids.forEach(eid => {
                let row = `
                    <tr>
                        <td>${eid.eid_name}</td>
                        <td>${eid.description}</td>
                        <td>${eid.num_profiles}</td>
                        <td>${eid.active_profile}</td>
                        <td>
                            <button class="btn btn-outline-secondary btn-sm view-profile"
                                data-eid="${eid.eid_name}">
                                View
                            </button>
                        </td>
                    </tr>
                `;
                tableBody.innerHTML += row;
            });
    
        } catch (error) {
            console.error("❌ Error loading EID list:", error);
        }
    }
    

    loadEidList();

    /** =================== View EID Profile Details =================== **/

    document.addEventListener("click", async function (event) {
        if (event.target.classList.contains("view-profile")) {
            event.preventDefault();
            
            let eid = event.target.getAttribute("data-eid");
            if (!eid) {
                console.error("❌ No EID found for this button.");
                return;
            }
    
            console.log(`📌 Loading profile page for EID: ${eid}`);
    
            // ✅ Ensure the page is properly loaded before fetching details
            await loadPage("profile-details.html", async function () {
                console.log(`✅ profile-details.html loaded. Fetching details for EID: ${eid}`);
                await loadEIDDetails(eid);
            });
        }
    });

    async function loadEIDDetails(eidName) {
        try {
            const response = await fetch(`${API_BASE_URL}/eid/${eidName}`, {
                method: "GET",
                mode: "cors",
                cache: "no-store",
                headers: { "Content-Type": "application/json" }
            });
    
            if (!response.ok) throw new Error("Failed to fetch EID details");
    
            const eidData = await response.json();
            console.log("✅ Loaded EID Details:", eidData);
    
            document.getElementById("profile-eid").innerText = `EID: ${eidData.eid_name}`;
            document.getElementById("profile-description").innerHTML = `<strong>Description:</strong> ${eidData.description}`;
            document.getElementById("profile-num-profiles").innerHTML = `<strong>Num of Installed Profile:</strong> ${eidData.num_profiles}`;
            document.getElementById("profile-active-profile").innerHTML = `<strong>Activated Profile:</strong> ${eidData.active_profile}`;
            document.getElementById("trigger-download-btn").setAttribute("data-eid", eidData.eid_name);
    
            populateActivationCodeTable(eidData.activation_codes);
    
        } catch (error) {
            console.error("❌ Error loading EID details:", error);
        }
    }
    

    /** =================== Trigger Download Profile =================== **/

    document.addEventListener("click", function (event) {
        if (event.target.classList.contains("trigger-download")) {
            event.preventDefault();
            let eid = event.target.getAttribute("data-eid");
            if (!eid) {
                alert("EID not found. Please try again.");
                return;
            }
            document.getElementById("trigger-eid").value = eid;
            let modalElement = new bootstrap.Modal(document.getElementById("triggerDownloadModal"));
            modalElement.show();
        }
    });

    /** =================== Submit Activation Code =================== **/

    document.addEventListener("click", function (event) {
        if (event.target.id === "submitActivationCode") {
            submitActivationCode();
        }
    });

    async function submitActivationCode() {
        let activationCode = document.getElementById("activationCodeInput").value.trim();
        let eid = document.getElementById("trigger-eid").value;
    
        if (!activationCode) {
            alert("Please enter an activation code.");
            return;
        }
    
        let activationData = {
            code: activationCode,
            iccid: "",
            state: "available",
        };
    
        try {
            let response = await fetch(`${API_BASE_URL}/eid/${eid}/add-activation`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(activationData),
                cache: "no-store"
            });
    
            if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
    
            alert("Activation code added successfully!");
    
            let modalElement = bootstrap.Modal.getInstance(document.getElementById("triggerDownloadModal"));
            modalElement.hide();
    
            await loadEIDDetails(eid); // ✅ Reload EID details to reflect new activation code
    
        } catch (error) {
            console.error("❌ Error adding activation code:", error);
            alert("Failed to add activation code. Please try again.");
        }
    }
    

    /** =================== Activation Code Table =================== **/

    function populateActivationCodeTable(activationCodes) {
        const tableBody = document.getElementById("activation-code-table");
        if (!tableBody) {
            console.error("❌ Activation code table not found!");
            return;
        }
    
        tableBody.innerHTML = ""; // ✅ Clear previous data
    
        activationCodes.forEach(code => {
            let row = `
                <tr>
                    <td>${code.code}</td>
                    <td>${code.iccid || "N/A"}</td>
                    <td><span class="badge bg-${getBadgeColor(code.state)}">${code.state.toUpperCase()}</span></td>
                    <td></td>
                </tr>
            `;
            tableBody.innerHTML += row;
        });
    }

    function getBadgeColor(state) {
        switch (state.toLowerCase()) {
            case "deleted": return "danger";
            case "available": return "warning";
            case "sent": return "info";
            case "complete": return "success";
            default: return "secondary";
        }
    }
});
