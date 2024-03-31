import { Text } from "@/shared";
import { Carousel, Label } from "flowbite-react";
import { useState } from "react";
// import { useNavigate, useParams, useSearchParams } from "react-router-dom";
import { infoType } from "@/entities";

const lostItemDetail = () => {
  //   const navigate = useNavigate();
  //   const { member } = useMemberStore();

  const [detailData] = useState<infoType>();

  //   const [query] = useSearchParams();
  //   const boardId = parseInt(useParams().id ?? "0");
  //   const [title, setTitle] = useState<string>("");
  //   const [content, setContent] = useState<string>("");

  return (
    <div className="flex flex-col flex-1 justify-center items-center p-[20px] relative">
      <div className="flex flex-row justify-between w-[340px]">
        <span className="bg-A706Blue2 text-A706CheryBlue text-xs font-bold me-2 px-2.5 py-0.5 rounded dark:bg-blue-900 dark:text-blue-300">
          {detailData?.board.categoryName ?? "카테고리 없음"}
        </span>
        <Text className="text-md font-bold">
          보관장소 : {detailData?.agencyName ?? "시설명"}
        </Text>
      </div>
      <div className="flex flex-col justify-center p-[40px] gap-[20px]">
        <div className="flex  items-center justify-center size-[300px]">
          <Carousel>
            {detailData?.board.imgUrls.map((imgUrl, idx) => (
              <div
                className="flex justify-center w-full h-full border border-A706Grey2 rounded-xl"
                key={idx}
              >
                <img
                  src={imgUrl}
                  alt="이미지가 없습니다."
                  className="object-fill rounded-xl"
                />
              </div>
            ))}
          </Carousel>
        </div>
      </div>
      <div className="w-[340px] flex flex-col text-center">
        <Text className="text-md">
          {detailData?.address + ", " + detailData?.agencyName}
        </Text>
        <p className="text-md font-bold">{detailData?.board.registeredAt}</p>
      </div>
      <div className="flex flex-row justify-between mt-10 w-[340px]">
        <div className="w-full">
          <Label color="secondary" value="물품명" />
          <Text className="text-lg font-bold">
            {detailData?.board.productName ?? "물품명"}
          </Text>
          <div className="h-[1px] bg-A706DarkGrey2"></div>
        </div>
      </div>
    </div>
  );
};

export default lostItemDetail;
