#!/usr/bin/env ruby
# encoding: utf-8

require "sinatra"
require "open-uri"
require "uri"
require "nokogiri"
require "json"
require "redis"

set :protection, :except=>:path_traversal

redis = Redis.new(url: ENV["REDIS_URL"] || "redis://localhost:6379")
# [Trabalho 4] Chave para ligar/desligar o cache Redis nos testes de carga
CACHE_ENABLED = %w[1 true yes].include?((ENV["CACHE_ENABLED"] || "true").downcase)
# [Trabalho 4] So para o teste de diagnostico: muda o limite de conexoes simultaneas do
# WEBrick (padrao 100). Sem a variavel, o servidor roda exatamente com a configuracao padrao.
set :server_settings, { MaxClients: Integer(ENV["WEBRICK_MAX_CLIENTS"]) } if ENV["WEBRICK_MAX_CLIENTS"]

Dir.mkdir("logs") unless Dir.exist?("logs")
cache_log = File.new("logs/extraction.log", "a")

get "/" do
  "Usage: http://<hostname>[:<prt>]/api/<url>"
end

get "/api/*" do
  url = [params['splat'].first, request.query_string].reject(&:empty?).join("?")
  cache_status = CACHE_ENABLED ? "HIT" : "OFF"
  jsonlinks = CACHE_ENABLED ? redis.get(url) : nil
  if jsonlinks.nil?
    cache_status = "MISS" if CACHE_ENABLED
    jsonlinks = JSON.pretty_generate(extract_links(url))
    redis.set(url, jsonlinks) if CACHE_ENABLED
  end

  cache_log.puts "#{Time.now.to_i}\t#{cache_status}\t#{url}"

  status 200
  headers "content-type" => "application/json"
  body jsonlinks
end

def extract_links(url)
  links = []
  # [Trabalho 4] Ruby >= 3.0 removeu o suporte a URLs em Kernel#open; URI.open e o equivalente
  doc = Nokogiri::HTML(URI.open(url))
  doc.css("a").each do |link|
    text = link.text.strip.split.join(" ")
    begin
      links.push({
        text: text.empty? ? "[IMG]" : text,
        href: URI.join(url, link["href"])
      })
    rescue
    end
  end
  links
end
