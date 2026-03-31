'use strict';

async function test_auth_token(username, password) {
    /*
    POST' \
        'http://localhost/auth/token' \
        -H 'accept: application/json' \
        -H 'Content-Type: application/x-www-form-urlencoded' \
        -d 'grant_type=password&username=string&password=********&scope=&client_id=string&client_secret=********'
    */
    // Use same-origin endpoint so it works with whichever host/port serves the page.
    const url = "http://127.0.0.1/auth/token";
    const data = new URLSearchParams();  // 创建 URLSearchParams 对象来构建表单数据
    data.append("grant_type", "password");
    data.append("username", username);
    data.append("password", password);

    try {
        const response = await window.fetch(url, {
            method: "POST",
            headers: {
                "accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded"
            },
            body: data
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        console.log("Token response:", result);
        return result;
    }catch (error) {
        console.error("Error fetching token:", error);
    }
}



export { test_auth_token };