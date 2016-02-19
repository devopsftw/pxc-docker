<?php
// vim: sw=4:ts=4:noet:sta:

use GuzzleHttp\Client;
use GuzzleHttp\Exception\RequestException;

class App {
	private $_http;

	private $_sid;

	public $service;

	public function __construct() {
		$this->_http = new Client([
			'base_url' => 'http://localhost:8500/',
			'defaults' => [ 'timeout' => 3 ],
		]);
	}

	public function createSession($attempt = 0) {
		$data = [
			'Name' => $this->service,
			'TTL' => '10s',
			'Checks' => [
				'serfHealth',
				'galera',
			],
		];
		try {
			$response = $this->_http->put('v1/session/create', [
				'json' => $data,
			]);
			$sid = $response->json()['ID'];
			return $sid;
		} catch (RequestException $e) {
			echo "failed to create session:\n" . $e->getMessage() . "\n";
			if ($attempt > 2) {
				throw $e;
			}
			echo "..Try to create session again";
			sleep(10);
			return $this->createSession($attempt + 1);
		}
	}

	public function renewSession() {
		$response = $this->_http->put("v1/session/renew/{$this->_sid}");
	}

	public function getKeyName() {
		return "election:{$this->service}";
	}

	public function acquireLock() {
		$key = urlencode($this->getKeyName());
		$response = $this->_http->put("v1/kv/{$key}", [ 'query' => [ 'acquire' => $this->_sid ] ]);
	}

	public function getKeyData() {
		$key = urlencode($this->getKeyName());
		$keyData = $this->_http->get("v1/kv/{$key}")->json()[0];
		return $keyData;
	}

	public function updateCheck() {
		$this->_http->get('v1/agent/check/pass/leader');
	}

	public function run() {
		$this->_sid = $this->createSession();
		echo "session id is: {$this->_sid}\n";

		while (true) {
			$this->acquireLock();

			$keyData = $this->getKeyData();
			if (isset($keyData['Session']) && $keyData['Session'] == $this->_sid) {
				$this->updateCheck();
				echo "acquired leadership, renew ttl check\n";
			} else {
				echo "no leadership\n";
			}
			sleep(10);
			$this->renewSession();
			echo microtime(true) . ' ' . "session renew\n";
		}
	}
}
