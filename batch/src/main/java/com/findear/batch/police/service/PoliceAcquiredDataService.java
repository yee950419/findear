package com.findear.batch.police.service;

import com.findear.batch.police.domain.PoliceAcquiredData;
import com.findear.batch.police.dto.SaveDataRequestDto;
import com.findear.batch.police.repository.PoliceAcquiredDataRepository;
import lombok.RequiredArgsConstructor;
import org.elasticsearch.action.search.SearchRequest;
import org.elasticsearch.action.search.SearchResponse;
import org.elasticsearch.client.RequestOptions;
import org.elasticsearch.client.RestHighLevelClient;
import org.elasticsearch.index.query.QueryBuilders;
import org.elasticsearch.search.SearchHit;
import org.elasticsearch.search.builder.SearchSourceBuilder;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;
import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;
import org.w3c.dom.NodeList;

import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;
import java.io.BufferedReader;
import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.util.*;

@RequiredArgsConstructor
@Service
public class PoliceAcquiredDataService {

    private final PoliceAcquiredDataRepository policeAcquiredDataRepository;

    private final RestHighLevelClient restHighLevelClient;

    @Value("${my.secret-key}")
    private String secretKey;

    private Long id = 1L;


    public void deleteDatas() {

        policeAcquiredDataRepository.deleteAll();
    }

    public List<PoliceAcquiredData> searchAllDatas() {

        try {

            List<PoliceAcquiredData> allDatas = new ArrayList<>();
            String searchAfter = null;
            int pageSize = 1000; // 페이지당 가져올 문서 수

            while (true) {
                SearchRequest searchRequest = new SearchRequest("police_acquired_data"); // Elasticsearch 인덱스 이름
                SearchSourceBuilder searchSourceBuilder = new SearchSourceBuilder();
                searchSourceBuilder.query(QueryBuilders.matchAllQuery());
                searchSourceBuilder.size(pageSize);

                if (searchAfter != null) {
                    searchSourceBuilder.sort("_doc");
                    searchSourceBuilder.searchAfter(new Object[]{searchAfter});
                }

                searchRequest.source(searchSourceBuilder);

                SearchResponse searchResponse = restHighLevelClient.search(searchRequest, RequestOptions.DEFAULT);

                SearchHit[] hits = searchResponse.getHits().getHits();
                if (hits.length == 0) {
                    break;
                }

                for (SearchHit hit : hits) {
                    allDatas.add(convertToPoliceData(hit));
                }

                // 다음 페이지를 가져오기 위해 검색 결과의 마지막 값을 설정
                searchAfter = hits[hits.length - 1].getId();
            }

            return allDatas;

        } catch (Exception e) {
            e.printStackTrace();
        }

        return null;

    }

    // 여기에서 SearchHit을 PoliceAcquiredData 객체로 변환하는 코드를 작성
    private PoliceAcquiredData convertToPoliceData(SearchHit hit) {


        Map<String, Object> sourceAsMap = hit.getSourceAsMap();

        PoliceAcquiredData policeAcquiredData;
        if(sourceAsMap.get("subPrdtClNm") != null) {

            policeAcquiredData = new PoliceAcquiredData(Long.parseLong(sourceAsMap.get("id").toString()),
                    sourceAsMap.get("atcId").toString(), sourceAsMap.get("depPlace").toString(),
                    sourceAsMap.get("fdFilePathImg").toString(), sourceAsMap.get("fdPrdtNm").toString(),
                    sourceAsMap.get("fdSbjt").toString(), sourceAsMap.get("clrNm").toString(),
                    sourceAsMap.get("fdYmd").toString(), sourceAsMap.get("prdtClNm").toString(),
                    sourceAsMap.get("mainPrdtClNm").toString(), sourceAsMap.get("subPrdtClNm").toString());
        } else {
            policeAcquiredData = new PoliceAcquiredData(Long.parseLong(sourceAsMap.get("id").toString()),
                    sourceAsMap.get("atcId").toString(), sourceAsMap.get("depPlace").toString(),
                    sourceAsMap.get("fdFilePathImg").toString(), sourceAsMap.get("fdPrdtNm").toString(),
                    sourceAsMap.get("fdSbjt").toString(), sourceAsMap.get("clrNm").toString(),
                    sourceAsMap.get("fdYmd").toString(), sourceAsMap.get("prdtClNm").toString(),
                    sourceAsMap.get("mainPrdtClNm").toString());
        }

        return policeAcquiredData;
    }

    public Page<PoliceAcquiredData> searchByPage(int page, int size) {

        return policeAcquiredDataRepository.findAll(PageRequest.of(page, size));
    }

    public void savePoliceData() {

        try {

            // elastic search 모든 데이터 삭제
            deleteDatas();

            // 요청을 보낼 링크 리스트 생성
            List<String> urlLinks = new ArrayList<>();

            String pageNo = "1";
            String numOfRows = "50000";

            /*URL*/
            String urlBuilder = "http://apis.data.go.kr/1320000/LosPtfundInfoInqireService/getPtLosfundInfoAccToClAreaPd" + "?" + URLEncoder.encode("serviceKey", StandardCharsets.UTF_8) + "=" + secretKey + /*Service Key*/
                    "&" + URLEncoder.encode("pageNo", StandardCharsets.UTF_8) + "=" + URLEncoder.encode("", StandardCharsets.UTF_8) + /*페이지번호*/
                    "&" + URLEncoder.encode("numOfRows", StandardCharsets.UTF_8) + "=" + URLEncoder.encode(numOfRows, StandardCharsets.UTF_8) + /*한 페이지 결과 수*/
                    "&" + URLEncoder.encode("PRDT_CL_CD_01", StandardCharsets.UTF_8) + "=" + URLEncoder.encode("", StandardCharsets.UTF_8) + /*대분류*/
                    "&" + URLEncoder.encode("PRDT_CL_CD_02", StandardCharsets.UTF_8) + "=" + URLEncoder.encode("", StandardCharsets.UTF_8) + /*중분류*/
                    "&" + URLEncoder.encode("CLR_CD", StandardCharsets.UTF_8) + "=" + URLEncoder.encode("", StandardCharsets.UTF_8) + /*습득물 색상*/
                    "&" + URLEncoder.encode("START_YMD", StandardCharsets.UTF_8) + "=" + URLEncoder.encode("20170302", StandardCharsets.UTF_8) + /*검색시작일*/
                    "&" + URLEncoder.encode("END_YMD", StandardCharsets.UTF_8) + "=" + URLEncoder.encode("20230802", StandardCharsets.UTF_8) + /*검색종료일*/
                    "&" + URLEncoder.encode("N_FD_LCT_CD", StandardCharsets.UTF_8) + "=" + URLEncoder.encode("", StandardCharsets.UTF_8); /*습득지역*/

            URL url = new URL(urlBuilder);
            HttpURLConnection conn = (HttpURLConnection) url.openConnection();
            conn.setRequestMethod("GET");
            conn.setRequestProperty("Content-type", "application/json");

            System.out.println("Response code: " + conn.getResponseCode());

            BufferedReader rd;
            if(conn.getResponseCode() >= 200 && conn.getResponseCode() <= 300) {
                rd = new BufferedReader(new InputStreamReader(conn.getInputStream()));
            } else {
                rd = new BufferedReader(new InputStreamReader(conn.getErrorStream()));
            }
            StringBuilder sb = new StringBuilder();
            String line;
            while ((line = rd.readLine()) != null) {
                sb.append(line);
            }
            rd.close();
            conn.disconnect();

            System.out.println(sb);

            List<String> responses = new ArrayList<>();
            responses.add(sb.toString());

            System.out.println("responses : ");

            for(String res : responses) {
                System.out.println(res);
            }

            // 업로드 및 lastTrs 업데이트 실행
            readandSaveData(responses);

        }
        catch (IOException e) {
            System.out.println(e.getMessage());
        }
    }

    /**
     * 각 속성값 문자열로 추출
     * @param responses
     * @return
     */
    private void readandSaveData(List<String> responses) {

        try {
            // 결과값 List
            List<String[]> rowDatas = new ArrayList<>();

            List<PoliceAcquiredData> policeAcquiredDataList = new ArrayList<>();

            DocumentBuilderFactory builderFactory = DocumentBuilderFactory.newInstance();
            DocumentBuilder builder = builderFactory.newDocumentBuilder();

            for (String response : responses) {

                System.out.println("response : " + response);

                // String -> document 변환
                Document xmlDoc = builder.parse(new ByteArrayInputStream(response.getBytes()));
                xmlDoc.getDocumentElement().normalize();

                Element root = xmlDoc.getDocumentElement();
                NodeList items = root.getElementsByTagName("item");

                // 데이터 읽어오기
                int length = items.getLength();

                String[] targetTagNames = {"atcId", "depPlace", "fdFilePathImg",
                        "fdPrdtNm", "fdSbjt", "fdYmd", "prdtClNm"};

                for (int i = 0; i < length; i++) {

                    PoliceAcquiredData policeAcquiredData;

                    Element item = (Element) items.item(i);
                    String[] rowData = new String[7];


                    for (int j = 0; j < targetTagNames.length; j++) {
                        Node valueNode = item.getElementsByTagName(targetTagNames[j]).item(0);
                        String value = (valueNode == null) ? null : valueNode.getTextContent();

                        System.out.println("value = " + value);

                        // null값 있는(잘못된) 데이터는 pass
                        if (value == null) continue;

                        rowData[j] = value.trim();

                    }

                    // 색상 컬럼 분류 로직
                    String fdSbjt = rowData[4];
                    String[] array = fdSbjt.split("\\(");
                    String clrNm = array[1];

                    // 대분류, 소분류 컬럼 분류 로직
                    String prdtClNm = rowData[6];
                    array = prdtClNm.split(" ");
                    String mainPrdtClNm = array[0];

                    String subPrdtClNm;
                    if(array.length != 3) {
                        subPrdtClNm = null;
                    }
                    else {

                        subPrdtClNm = array[2];
                    }

                    policeAcquiredData = new PoliceAcquiredData(id++,
                            rowData[0], rowData[1], rowData[2], rowData[3], rowData[4],
                            clrNm, rowData[5], rowData[6], mainPrdtClNm, subPrdtClNm);

                    policeAcquiredDataList.add(policeAcquiredData);

                }

                policeAcquiredDataRepository.saveAll(policeAcquiredDataList);

            }

        } catch (Exception e) {
            e.printStackTrace();
        }
    }

}