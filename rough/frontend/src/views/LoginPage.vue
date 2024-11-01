<template>
    <NavBar />
    <div class="container mt-5">
        <h2>Login</h2>
        <form @submit.prevent="login">
            <div class="mb-3">
                <label for="username" class="form-label">Username</label>
                <input v-model="username" type="username" class="form-control" id="username" required>
            </div>
            <div class="mb-3">
                <label for="password" class="form-label">Password</label>
                <input v-model="password" type="password" class="form-control" id="password" required>
            </div>
            <button type="submit" class="btn btn-primary">Submit</button>
        </form>
    </div>
</template>

<script>
import NavBar from '@/components/NavBar.vue'
export default {
    components: {
        NavBar
    }, 
    name: "LoginPage",
    data() {
        return {
            username: '',
            password: ''
        }
    },
    methods: {
        async login() {
            const response = await fetch('http://127.0.0.1:5000/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    username: this.username,
                    password: this.password
                })
                
            })
            const data = await response.json()
            console.log(data)
            if (!response.ok) {
                alert(data.error)
            }
            else {
                alert(data.message)
                // storing an item in local storage
                localStorage.setItem('access_token', data.access_token)
                // const token = localStorage.getItem('token')
                // console.log(token)
                this.$router.push('/')
            }
        }
    }
}

</script>