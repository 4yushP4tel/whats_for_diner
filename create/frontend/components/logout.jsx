import React from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";

export const Logout = ({setStatus}) => {
    const navigate = useNavigate();
    
    const handleLogout = async () => {
        try {
            await axios.post("/api/logout", { withCredentials: true });
            const authResponse = await axios.get("/api/check_auth", {withCredentials: true});
            const authStatus = authResponse.data.auth_status;
            setStatus(authStatus);
            navigate("/");
            console.log(authStatus)
        } catch (error) {
            console.log("Error logging out: ", error);
        }}

    return(
        <button className = "logout_button" onClick={handleLogout}>Logout</button>
    );
};