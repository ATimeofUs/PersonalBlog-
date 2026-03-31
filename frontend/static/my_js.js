'use strict';

import { test_auth_token } from "./api_auth.js";

console.log("Hello, this is my_js.js!");

const loginForm = document.getElementById('loginForm');

loginForm.addEventListener('submit', async function(event) {
    // 阻止表单默认提交行为
    event.preventDefault();

    // 获取输入的用户名和密码
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    // 异步调用测试认证函数
    const res = await test_auth_token(username, password);
    console.log(res);
});