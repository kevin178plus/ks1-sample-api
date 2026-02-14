<?php
/**
 * KUAE Cloud Coding Plan - OpenAI Compatible Local API Proxy
 * PHP 7.4+
 */

error_reporting(E_ALL);
ini_set('display_errors', '0');

class KuaeCloudLocalAPI {
    private $config;
    private $apiKey;
    private $baseUrl = 'https://coding-plan-endpoint.kuaecloud.net/v1';
    private $model = 'GLM-4.7';
    private $debug = false;
    private $logFile = 'api.log';

    public function __construct() {
        $this->loadConfig();
    }

    private function loadConfig() {
        // Load from .env file
        $envFile = __DIR__ . '/.env';
        if (file_exists($envFile)) {
            $envLines = file($envFile, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
            foreach ($envLines as $line) {
                if (strpos(trim($line), '#') === 0) {
                    continue; // Skip comments
                }
                if (strpos($line, '=') !== false) {
                    list($key, $value) = explode('=', $line, 2);
                    if (trim($key) === 'kuaecloud_coding_plan') {
                        $this->apiKey = trim($value);
                        break;
                    }
                }
            }
        }
        
        // Fallback to api-key.ini for backward compatibility
        if (empty($this->apiKey)) {
            $configFile = __DIR__ . '/api-key.ini';
            if (file_exists($configFile)) {
                $this->config = parse_ini_file($configFile, true);
                if (isset($this->config['key']['kuaecloud-coding_plan'])) {
                    $this->apiKey = $this->config['key']['kuaecloud-coding_plan'];
                }
            }
        }
        
        $this->debug = getenv('DEBUG') === 'true' || (isset($this->config['debug']) && $this->config['debug']);
    }

    private function log($message, $data = []) {
        if ($this->debug) {
            $log = [
                'time' => date('Y-m-d H:i:s'),
                'message' => $message,
                'data' => $data
            ];
            file_put_contents($this->logFile, json_encode($log, JSON_UNESCAPED_UNICODE) . "\n", FILE_APPEND);
        }
    }

    private function jsonResponse($data, $statusCode = 200) {
        http_response_code($statusCode);
        header('Content-Type: application/json');
        echo json_encode($data, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
        exit;
    }

    private function errorResponse($message, $code = 'invalid_request_error', $statusCode = 400) {
        $this->log('Error', ['code' => $code, 'message' => $message]);
        $this->jsonResponse([
            'error' => [
                'message' => $message,
                'type' => $code,
                'param' => null
            ]
        ], $statusCode);
    }

    private function authenticate() {
        $headers = getallheaders();
        $authHeader = isset($headers['Authorization']) ? $headers['Authorization'] : '';

        if (!$authHeader) {
            $authHeader = isset($headers['authorization']) ? $headers['authorization'] : '';
        }

        if (preg_match('/Bearer\s+(.+)/i', $authHeader, $matches)) {
            $token = $matches[1];
        } else {
            $token = '';
        }

        $this->log('Auth attempt', ['token_provided' => !empty($token)]);

        if (empty($token) || $token !== $this->apiKey) {
            $this->errorResponse('Invalid API key', 'invalid_api_key', 401);
        }
    }

    public function handleRequest() {
        $this->log('Request', [
            'method' => $_SERVER['REQUEST_METHOD'],
            'uri' => $_SERVER['REQUEST_URI']
        ]);

        if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
            $this->errorResponse('Only POST method is supported', 'invalid_request_error', 405);
        }

        $this->authenticate();

        $input = file_get_contents('php://input');
        $data = json_decode($input, true);

        if (json_last_error() !== JSON_ERROR_NONE) {
            $this->errorResponse('Invalid JSON in request body', 'invalid_request_error', 400);
        }

        if (!isset($data['messages']) || !is_array($data['messages'])) {
            $this->errorResponse('Missing or invalid messages field', 'invalid_request_error', 400);
        }

        $model = $data['model'] ?? $this->model;
        $messages = $data['messages'];
        $maxTokens = $data['max_tokens'] ?? 4096;
        $temperature = $data['temperature'] ?? 0.7;

        $this->log('Chat request', [
            'model' => $model,
            'message_count' => count($messages),
            'max_tokens' => $maxTokens,
            'temperature' => $temperature
        ]);

        $result = $this->callKuaeCloudAPI($model, $messages, $maxTokens, $temperature);
        $this->jsonResponse($result);
    }

    private function callKuaeCloudAPI($model, $messages, $maxTokens, $temperature) {
        $url = $this->baseUrl . '/chat/completions';

        $payload = [
            'model' => $model,
            'messages' => $messages,
            'max_tokens' => $maxTokens,
            'temperature' => $temperature
        ];

        $this->log('Calling KuaeCloud API', ['url' => $url]);

        $ch = curl_init($url);
        curl_setopt_array($ch, [
            CURLOPT_POST => true,
            CURLOPT_POSTFIELDS => json_encode($payload),
            CURLOPT_HTTPHEADER => [
                'Content-Type: application/json',
                'Authorization: Bearer ' . $this->apiKey
            ],
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_TIMEOUT => 120,
            CURLOPT_CONNECTTIMEOUT => 30,
            CURLOPT_SSL_VERIFYPEER => false,
            CURLOPT_SSL_VERIFYHOST => 0
        ]);

        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        $error = curl_error($ch);
        curl_close($ch);

        if ($error) {
            $this->log('CURL error', ['error' => $error]);
            $this->errorResponse('API request failed: ' . $error, 'api_error', 500);
        }

        $this->log('KuaeCloud response', ['http_code' => $httpCode, 'response_length' => strlen($response)]);

        $result = json_decode($response, true);

        if (json_last_error() !== JSON_ERROR_NONE) {
            $this->log('Invalid JSON from KuaeCloud', ['response' => substr($response, 0, 500)]);
            $this->errorResponse('Invalid response from upstream API', 'api_error', 500);
        }

        if ($httpCode !== 200) {
            $errorMsg = $result['error']['message'] ?? 'Unknown error';
            $this->log('KuaeCloud error', ['code' => $httpCode, 'message' => $errorMsg]);
            $this->errorResponse('Upstream API error: ' . $errorMsg, 'api_error', $httpCode);
        }

        return $result;
    }
}

if (php_sapi_name() !== 'cli') {
    $api = new KuaeCloudLocalAPI();
    $api->handleRequest();
}
