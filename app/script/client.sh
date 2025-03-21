#!/bin/bash

# 配置区域
SERVER_IP="192.168.1.173"
KNOCK_SEQUENCE=(
    "5331 tcp"
    "62345 udp"
    "2453 tcp"
    "8823 udp"
)
FTP_DATA_PORT=20
MD5_LENGTH=32

# 依赖检测与安装
check_dependencies() {
    declare -A tools=(
        ["nping"]="nmap"
        ["hping3"]="hping3"
        ["md5sum"]="coreutils"
    )

    for cmd in "${!tools[@]}"; do
        if ! command -v $cmd &> /dev/null; then
            echo "正在安装依赖: ${tools[$cmd]}"
            
            # 自动识别发行版
            if command -v apt-get &> /dev/null; then
                sudo apt-get update
                sudo apt-get install -y ${tools[$cmd]}
            elif command -v yum &> /dev/null; then
                sudo yum install -y ${tools[$cmd]}
            elif command -v dnf &> /dev/null; then
                sudo dnf install -y ${tools[$cmd]}
            elif command -v zypper &> /dev/null; then
                sudo zypper install -y ${tools[$cmd]}
            else
                echo "不支持的Linux发行版"
                exit 1
            fi

            # 二次验证安装
            if ! command -v $cmd &> /dev/null; then
                echo "依赖安装失败: $cmd"
                exit 1
            fi
        fi
    done
}

# 协议伪装发送函数
send_ftp_data() {
    local port=$1
    local payload=$2
    
    # 优先使用nping，其次hping3
    if command -v nping &> /dev/null; then
        sudo nping --tcp -p $port --flags "PSH,ACK" --source-port $FTP_DATA_PORT \
            --data-string "$payload" $SERVER_IP --rate 1 --count 1 -H \
            | grep -q "RCVD" && return 0 || return 1
    else
        sudo hping3 $SERVER_IP -p $port -s $FTP_DATA_PORT -M 2147 -L 2147 \
            -d ${#payload} -E /dev/stdin -t 128 -c 1 <<< "$payload" \
            | grep -q "flags=SA" && return 0 || return 1
    fi
}

# UDP发送函数
send_udp() {
    local port=$1
    local payload=$2
    
    echo -n "$payload" | nc -u -w1 -q1 -s $(hostname -I | awk '{print $1}') \
        $SERVER_IP $port 2>/dev/null
    return $?
}

# 密码处理
get_password() {
    while true; do
        read -sp "请输入认证密码: " password
        echo
            md5_hash=$(echo -n "$password" | md5sum | awk '{print $1}')
            [ ${#md5_hash} -eq $MD5_LENGTH ] && break || echo "MD5生成失败"
    done
    unset password
}

# 主逻辑
main() {
    check_dependencies
    get_password
    
    local total=${#KNOCK_SEQUENCE[@]}
    local count=0
    
    for knock in "${KNOCK_SEQUENCE[@]}"; do
        ((count++))
        IFS=' ' read -r port proto <<< "$knock"
        proto=${proto,,}
        
        # 构造载荷
        if [ $count -eq $total ]; then
            payload=$md5_hash
            echo "[*] 正在发送认证载荷到$proto/$port"
        else
            payload="220 FTP server ready\r\n"
        fi

        case $proto in
            tcp)
                if send_ftp_data $port "$payload"; then
                    echo "[+] TCP/$port 伪装成功"
                else
                    echo "[!] TCP/$port 发送失败"
                    exit 1
                fi
                ;;
            udp)
                if send_udp $port "$payload"; then
                    echo "[+] UDP/$port 发送成功"
                else
                    echo "[!] UDP/$port 发送失败"
                    exit 1
                fi
                ;;
            *)
                echo "[!] 无效协议: $proto"
                exit 1
                ;;
        esac
        
        # 随机延时
        sleep $(( RANDOM % 3 + 1 ))
    done
    
    echo "[√] 所有敲门序列完成"
}

# 执行入口
if [ "$(id -u)" -ne 0 ]; then
    echo "需要root权限运行"
    exit 1
fi
main
