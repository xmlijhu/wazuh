#include "api/wazuhRequest.hpp"

#include <logging/logging.hpp>

namespace api
{
/*
 * https://github.com/wazuh/wazuh/issues/5934
 */
std::optional<std::string> WazuhRequest::validate() const
{
    if (!m_jrequest.isObject())
    {
        return "The request must be formatted as a JSON object";
    }
    if (!m_jrequest.exists("/version") || !m_jrequest.isInt("/version"))
    {
        return "The request must have a \"version\" field containing an integer value";
    }
    // Check if the version is supported
    if (m_jrequest.getInt("/version").value() != VERSION_SUPPORTED)
    {
        return fmt::format(
            "The request version ({}) is not supported, the supported version is {}",
            m_jrequest.getInt("/version").value(),
            VERSION_SUPPORTED);
    }
    if (!m_jrequest.isString("/command"))
    {
        return "The request must have a command field containing a string value";
    }
    if (!m_jrequest.isObject("/parameters"))
    {
        return "The request must have a parameters field with a JSON object value";
    }
    if (!m_jrequest.isObject("/origin"))
    {
        return "The request must have an origin field with a JSON object value";
    }
    if (!m_jrequest.isString("/origin/name"))
    {
        return "The request must have an origin/name field with a string value";
    }
    if (!m_jrequest.isString("/origin/module"))
    {
        return "The request must have an origin/module field with a string value";
    }

    return std::nullopt;
}

WazuhRequest WazuhRequest::create(std::string_view command,
                                  std::string_view originName,
                                  const json::Json& parameters)
{

    if (command.empty())
    {
        WAZUH_LOG_DEBUG(
            "Engine API request: \"{}\" method: command: \"{}\", origin name: "
            "\"{}\", parameters: \"{}\".",
            __func__,
            command,
            originName,
            parameters.str());

        throw std::runtime_error("The command cannot be empty");
    }
    if (!parameters.isObject())
    {
        WAZUH_LOG_DEBUG(
            "Engine API request: \"{}\" method: command: \"{}\", origin name: "
            "\"{}\", parameters: \"{}\".",
            __func__,
            command,
            originName,
            parameters.str());

        throw std::runtime_error(
            "The command parameters must be inside of a JSON object");
    }

    json::Json jrequest;
    jrequest.setInt(VERSION_SUPPORTED, "/version");
    jrequest.setString(command, "/command");
    jrequest.set("/parameters", parameters);
    jrequest.setString("wazuh-engine", "/origin/module");
    jrequest.setString(originName, "/origin/name");

    return WazuhRequest(jrequest);
}

} // namespace api