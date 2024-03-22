package com.findear.main.Alarm.controller;

import com.findear.main.Alarm.dto.AlarmDataDto;
import com.findear.main.Alarm.dto.ShowAlarmDto;
import com.findear.main.Alarm.service.AlarmService;
import com.findear.main.Alarm.service.EmitterService;
import com.findear.main.common.response.SuccessResponse;
import com.findear.main.member.query.service.MemberQueryService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import java.nio.charset.StandardCharsets;
import java.time.LocalDateTime;
import java.util.List;

@Slf4j
@RequiredArgsConstructor
@RestController
public class AlarmController {

    private final EmitterService emitterService;
    private final AlarmService alarmService;

    @GetMapping(value = "/subscribe/{memberId}", produces = "text/event-stream; charset=UTF-8")
    public SseEmitter subscribe(@PathVariable Long memberId) {

        SseEmitter result = emitterService.subscribe(memberId);

        return result;
    }

    @PostMapping("/send-data/{memberId}")
    public void sendDataTest(@PathVariable Long memberId, @RequestBody AlarmDataDto alarmDataDto) {

        alarmDataDto.setGeneratedAt(LocalDateTime.now());
        emitterService.alarm(memberId, alarmDataDto, "알림 갔니 인성아", "message");
    }

    @GetMapping("/alarm-list")
    public ResponseEntity<?> showAlarmList() {

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(new MediaType("application", "json", StandardCharsets.UTF_8));

        Long memberId = MemberQueryService.getAuthenticatedMemberId();

        List<AlarmDataDto> result = alarmService.showAlarmList(memberId);

        return ResponseEntity.ok().body(new SuccessResponse(HttpStatus.OK.value(), "알림 리스트를 조회하였습니다.", result));
    }

    @GetMapping("/alarm/{alarmId}")
    public ResponseEntity<?> showAlarm(@PathVariable Long alarmId) {

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(new MediaType("application", "json", StandardCharsets.UTF_8));

        Long memberId = MemberQueryService.getAuthenticatedMemberId();
        ShowAlarmDto showAlarmDto = ShowAlarmDto.builder().memberId(memberId).alarmId(alarmId).build();

        AlarmDataDto result = alarmService.showAlarm(showAlarmDto);

        return ResponseEntity.ok().body(new SuccessResponse(HttpStatus.OK.value(), "알림을 조회하였습니다.", result));
    }

}
