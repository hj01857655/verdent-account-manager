const axios = require('axios');

class VerdentAPI {
  constructor(options = {}) {
    this.host = options.host || 'agent.verdent.ai';
    this.port = options.port || 443;
    this.loginHost = options.loginHost || 'login.verdent.ai';
    this.logHost = options.logHost || 'log.verdent.ai';
    this.token = options.token || null;
    this.timeout = options.timeout || 10000;
    
    const protocol = this.port === 443 ? 'https' : 'http';
    const portSuffix = (this.port === 443 || this.port === 80) ? '' : `:${this.port}`;
    this.baseURL = `${protocol}://${this.host}${portSuffix}`;
    this.loginURL = `https://${this.loginHost}`;
    this.logURL = `https://${this.logHost}`;
    
    this.wsProtocol = this.port === 443 ? 'wss' : 'ws';
    this.wsURL = `${this.wsProtocol}://${this.host}${portSuffix}/chat`;
  }

  setToken(token) {
    this.token = token;
  }

  getHeaders() {
    const headers = {};
    if (this.token) {
      headers.Cookie = `token=${this.token}`;
    }
    return headers;
  }

  getAxiosInstance(baseURL = null) {
    return axios.create({
      baseURL: baseURL || this.baseURL,
      timeout: this.timeout,
      headers: this.getHeaders()
    });
  }

  async login(code, codeVerifier) {
    try {
      const client = this.getAxiosInstance(this.loginURL);
      const response = await client.post('/passport/pkce/callback', {
        code,
        codeVerifier
      });
      
      if (response.data?.data?.token) {
        this.token = response.data.data.token;
        return this.token;
      }
      throw new Error('Token not found in response');
    } catch (error) {
      console.error('Login failed:', error.message);
      throw error;
    }
  }

  async fetchUserInfo() {
    try {
      const client = this.getAxiosInstance();
      const response = await client.get('/user/center/info');
      return response.data?.data;
    } catch (error) {
      console.error('Failed to fetch user info:', error.message);
      throw error;
    }
  }

  async getInputBoxInfo(version) {
    try {
      const client = this.getAxiosInstance();
      const response = await client.get('/input_box/info', {
        params: { version }
      });
      return response.data?.data;
    } catch (error) {
      console.error('Failed to get input box info:', error.message);
      throw error;
    }
  }

  async uploadFile(fileData, filename) {
    try {
      const client = this.getAxiosInstance();
      const formData = new FormData();
      formData.append('file', fileData, filename);
      
      const response = await client.post('/user/center/upload_file', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      return response.data?.data;
    } catch (error) {
      console.error('Failed to upload file:', error.message);
      throw error;
    }
  }

  async submitFeedback(feedbackData) {
    try {
      const client = this.getAxiosInstance();
      const response = await client.post('/user/center/feedback', feedbackData);
      return response.data?.data;
    } catch (error) {
      console.error('Failed to submit feedback:', error.message);
      throw error;
    }
  }

  async getUserCredits() {
    try {
      const userInfo = await this.fetchUserInfo();
      return {
        consumed: userInfo.tokenInfo?.tokenConsumed || 0,
        free: userInfo.tokenInfo?.tokenFree || 0,
        total: (userInfo.tokenInfo?.tokenFree || 0) - (userInfo.tokenInfo?.tokenConsumed || 0)
      };
    } catch (error) {
      console.error('Failed to get user credits:', error.message);
      throw error;
    }
  }

  async getUserEmail() {
    try {
      const userInfo = await this.fetchUserInfo();
      return userInfo.email;
    } catch (error) {
      console.error('Failed to get user email:', error.message);
      throw error;
    }
  }

  getWebSocketURL() {
    return this.wsURL;
  }

  getWebSocketHeaders() {
    return this.getHeaders();
  }
}

module.exports = VerdentAPI;
