package com.findear.main.board.command.controller;

import com.findear.main.board.command.service.BoardCommandService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@Slf4j
@RequiredArgsConstructor
@RequestMapping("/board")
@RestController
public class BoardCommandController {

    private final BoardCommandService boardCommandService;


}