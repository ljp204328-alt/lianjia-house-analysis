<template>
  <div class="login-container">
    <div class="login-box">
      <div class="login-header">
        <h2>链家网租房数据分析系统</h2>
        <p>用户登录</p>
      </div>
      
      <form @submit.prevent="handleLogin" class="login-form">
        <div class="form-item">
          <label>用户名</label>
          <input 
            type="text" 
            v-model="loginForm.username" 
            placeholder="请输入用户名"
            required
          />
        </div>
        
        <div class="form-item">
          <label>密码</label>
          <input 
            type="password" 
            v-model="loginForm.password" 
            placeholder="请输入密码"
            required
          />
        </div>
        
        <div class="form-actions">
          <button type="submit" class="btn-login" :disabled="loading">
            {{ loading ? '登录中...' : '登 录' }}
          </button>
          <button type="button" class="btn-register" @click="showRegister = true">
            注 册
          </button>
        </div>
        
        <div v-if="errorMessage" class="error-msg">{{ errorMessage }}</div>
      </form>
    </div>

    <!-- 注册弹窗 -->
    <div v-if="showRegister" class="modal-overlay" @click.self="showRegister = false">
      <div class="modal-box">
        <div class="modal-header">
          <h3>用户注册</h3>
          <button class="close-btn" @click="showRegister = false">×</button>
        </div>
        
        <form @submit.prevent="handleRegister" class="register-form">
          <div class="form-item">
            <label>用户名</label>
            <input 
              type="text" 
              v-model="registerForm.username" 
              placeholder="请输入用户名"
              required
            />
          </div>
          
          <div class="form-item">
            <label>密码</label>
            <input 
              type="password" 
              v-model="registerForm.password" 
              placeholder="请输入密码(至少6位)"
              required
            />
          </div>
          
          <div class="form-item">
            <label>确认密码</label>
            <input 
              type="password" 
              v-model="registerForm.password2" 
              placeholder="请再次输入密码"
              required
            />
          </div>
          
          <div class="form-item">
            <label>手机号(可选)</label>
            <input 
              type="tel" 
              v-model="registerForm.phone" 
              placeholder="请输入手机号"
            />
          </div>
          
          <button type="submit" class="btn-submit" :disabled="loading">
            {{ loading ? '注册中...' : '注 册' }}
          </button>
          
          <div v-if="registerMessage" :class="['msg', registerSuccess ? 'success' : 'error']">
            {{ registerMessage }}
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script>
import request from '@/utils/request'

export default {
  name: 'Login',
  data() {
    return {
      loginForm: {
        username: '',
        password: ''
      },
      registerForm: {
        username: '',
        password: '',
        password2: '',
        phone: ''
      },
      loading: false,
      errorMessage: '',
      showRegister: false,
      registerMessage: '',
      registerSuccess: false
    }
  },
  methods: {
    async handleLogin() {
      this.loading = true
      this.errorMessage = ''
      
      try {
        const response = await request.post('/users/login/', this.loginForm)
        
        if (response.data.code === 200) {
          // 保存token到localStorage
          localStorage.setItem('token', response.data.data.token)
          localStorage.setItem('user_id', response.data.data.user_id)
          localStorage.setItem('username', response.data.data.username)
          
          // 跳转到首页
          this.$router.push('/home')
        } else {
          this.errorMessage = response.data.message || '登录失败'
        }
      } catch (error) {
        this.errorMessage = error.response?.data?.message || '网络错误,请检查后端服务是否启动'
      } finally {
        this.loading = false
      }
    },
    
    async handleRegister() {
      this.loading = true
      this.registerMessage = ''
      
      if (this.registerForm.password !== this.registerForm.password2) {
        this.registerMessage = '两次密码不一致'
        this.registerSuccess = false
        this.loading = false
        return
      }
      
      try {
        const response = await request.post('/users/register/', this.registerForm)
        
        if (response.data.code === 200) {
          this.registerMessage = '注册成功!请登录'
          this.registerSuccess = true
          
          // 清空表单
          this.registerForm = {
            username: '',
            password: '',
            password2: '',
            phone: ''
          }
          
          // 3秒后关闭注册窗口
          setTimeout(() => {
            this.showRegister = false
            this.registerMessage = ''
          }, 2000)
        } else {
          this.registerMessage = response.data.message || '注册失败'
          this.registerSuccess = false
        }
      } catch (error) {
        this.registerMessage = error.response?.data?.message || '网络错误'
        this.registerSuccess = false
      } finally {
        this.loading = false
      }
    }
  }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.login-box {
  background: white;
  border-radius: 12px;
  padding: 40px;
  width: 100%;
  max-width: 420px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
}

.login-header {
  text-align: center;
  margin-bottom: 30px;
}

.login-header h2 {
  color: #333;
  font-size: 24px;
  margin-bottom: 8px;
}

.login-header p {
  color: #666;
  font-size: 16px;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-item label {
  color: #333;
  font-size: 14px;
  font-weight: 500;
}

.form-item input {
  padding: 12px 16px;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  font-size: 14px;
  transition: all 0.3s;
}

.form-item input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.form-actions {
  display: flex;
  gap: 12px;
  margin-top: 10px;
}

.btn-login,
.btn-register,
.btn-submit {
  flex: 1;
  padding: 12px;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-login {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.btn-login:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
}

.btn-register {
  background: #f0f0f0;
  color: #666;
}

.btn-register:hover {
  background: #e0e0e0;
}

.btn-submit {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  margin-top: 10px;
}

.btn-submit:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
}

button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.error-msg {
  color: #f44336;
  font-size: 14px;
  text-align: center;
  margin-top: 10px;
}

/* 注册弹窗样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-box {
  background: white;
  border-radius: 12px;
  padding: 30px;
  width: 100%;
  max-width: 420px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.modal-header h3 {
  color: #333;
  font-size: 20px;
  margin: 0;
}

.close-btn {
  background: none;
  border: none;
  font-size: 28px;
  color: #999;
  cursor: pointer;
  padding: 0;
  width: 30px;
  height: 30px;
  line-height: 1;
}

.close-btn:hover {
  color: #333;
}

.register-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.msg {
  padding: 10px;
  border-radius: 6px;
  text-align: center;
  font-size: 14px;
}

.msg.success {
  background: #e8f5e9;
  color: #4caf50;
}

.msg.error {
  background: #ffebee;
  color: #f44336;
}
</style>
