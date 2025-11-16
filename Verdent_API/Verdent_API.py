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
import requests
from typing import Optional, Dict, Any
from urllib.parse import urlencode


class VerdentAPI:
    def __init__(
        self,
        host: str = 'agent.verdent.ai',
        port: int = 443,
        login_host: str = 'login.verdent.ai',
        log_host: str = 'log.verdent.ai',
        token: Optional[str] = None,
        timeout: int = 10
    ):
        self.host = host
        self.port = port
        self.login_host = login_host
        self.log_host = log_host
        self.token = token
        self.timeout = timeout
        
        protocol = 'https' if port == 443 else 'http'
        port_suffix = '' if port in [443, 80] else f':{port}'
        self.base_url = f'{protocol}://{host}{port_suffix}'
        self.login_url = f'https://{login_host}'
        self.log_url = f'https://{log_host}'
        
        self.ws_protocol = 'wss' if port == 443 else 'ws'
        self.ws_url = f'{self.ws_protocol}://{host}{port_suffix}/chat'
    
    def set_token(self, token: str) -> None:
        self.token = token
    
    def get_headers(self) -> Dict[str, str]:
        headers = {}
        if self.token:
            headers['Cookie'] = f'token={self.token}'
        return headers
    
    def login(self, code: str, code_verifier: str) -> str:
        try:
            url = f'{self.login_url}/passport/pkce/callback'
            response = requests.post(
                url,
                json={'code': code, 'codeVerifier': code_verifier},
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            if data.get('data', {}).get('token'):
                self.token = data['data']['token']
                return self.token
            raise Exception('Token not found in response')
        except Exception as e:
            print(f'Login failed: {str(e)}')
            raise
    
    def fetch_user_info(self) -> Dict[str, Any]:
        try:
            url = f'{self.base_url}/user/center/info'
            response = requests.get(
                url,
                headers=self.get_headers(),
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            return data.get('data', {})
        except Exception as e:
            print(f'Failed to fetch user info: {str(e)}')
            raise
    
    def get_input_box_info(self, version: str) -> Dict[str, Any]:
        try:
            url = f'{self.base_url}/input_box/info?{urlencode({"version": version})}'
            response = requests.get(
                url,
                headers=self.get_headers(),
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            return data.get('data', {})
        except Exception as e:
            print(f'Failed to get input box info: {str(e)}')
            raise
    
    def upload_file(self, file_data: bytes, filename: str) -> Dict[str, Any]:
        try:
            url = f'{self.base_url}/user/center/upload_file'
            files = {'file': (filename, file_data)}
            headers = self.get_headers()
            
            response = requests.post(
                url,
                files=files,
                headers=headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            return data.get('data', {})
        except Exception as e:
            print(f'Failed to upload file: {str(e)}')
            raise
    
    def submit_feedback(self, feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            url = f'{self.base_url}/user/center/feedback'
            response = requests.post(
                url,
                json=feedback_data,
                headers=self.get_headers(),
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            return data.get('data', {})
        except Exception as e:
            print(f'Failed to submit feedback: {str(e)}')
            raise
    
    def get_user_credits(self) -> Dict[str, int]:
        try:
            user_info = self.fetch_user_info()
            token_info = user_info.get('tokenInfo', {})
            consumed = token_info.get('tokenConsumed', 0)
            free = token_info.get('tokenFree', 0)
            
            return {
                'consumed': consumed,
                'free': free,
                'total': free - consumed
            }
        except Exception as e:
            print(f'Failed to get user credits: {str(e)}')
            raise
    
    def get_user_email(self) -> str:
        try:
            user_info = self.fetch_user_info()
            return user_info.get('email', '')
        except Exception as e:
            print(f'Failed to get user email: {str(e)}')
            raise
    
    def get_websocket_url(self) -> str:
        return self.ws_url
    
    def get_websocket_headers(self) -> Dict[str, str]:
        return self.get_headers()
